#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
"""
Support for server-side tracking/resolving of delclared dependencies
between javascript 'modules'
"""
import sys, os
import re

from cStringIO import StringIO

# path to the directory containing the runtime js file modular_rt.js
jsDir = os.path.join(os.path.dirname(__file__), 'js')

use_rx = re.compile(r"(?:JSAN|OpenEnd).use\((['\"][^'\"]*['\"]).*\)", re.MULTILINE)
require_rx = re.compile(r"OpenEnd.require\((['\"][^'\"]*['\"])\)", re.MULTILINE)
deps_rx = re.compile(r"Base._deps\(.*(\[.*\]).*\)", re.MULTILINE)

from htmlrewrite import HTMLRewriter, rewrite_html

def _topSort(deps):
    res = []
    counts = {}
    def add(group):
        for el in group:
            counts[el] = counts.get(el, 0) + 1
    def remove(group):
        for el in group:
            counts[el] -= 1
            if counts[el] == 0:
                del counts[el]
    for group in deps.itervalues():
        add(group)

    while deps:
        free = [cand for cand in deps if cand not in counts]
        assert free, deps
        for el in free:
            group = deps.pop(el)
            remove(group)
            res.append(el)
    res.reverse()
    return res

class FP(object):
    # minimal filepath object

    def __init__(self, path):
        self.path = path

    def open(self, mode='r'):
        return open(self.path, mode)

    def getmtime(self):
        return os.stat(self.path).st_mtime

    def exists(self):
        return os.path.exists(self.path)
                                  
class JsResolver(object):

    def __init__(self, repoParents=None, defaultRepos=None):
        self._depsData = {}
        self.defaultRepos = defaultRepos
        repoParents = repoParents or {}
        self.setRepoParents(repoParents)

    def setRepoParents(self, repoParents):
        self._parents = {}        
        for uri, directory in repoParents.items():
            if uri[-1] == '/':
                uri = uri[:-1]
            segs = uri.split('/')[1:]
            self._parents[directory] = segs

    def _findDeps(self, module, fsRepos):
        deps = {}
        self._simpleDeps(module, fsRepos, deps)
        return _topSort(deps)

    def _findFP(self, segs):
        # I map uri segs to a directory in the file system containing the
        # actual js files
        # use setRepoParents or override me
        for directory, parent in self._parents.items():
            if segs[:len(parent)] == parent:
                return FP(os.path.join(directory, *segs[len(parent):]))
        return None

    def _findReposInFS(self, repos):
        repos = [repo.split('/')[1:] for repo in repos if repo]
        for repo in repos:
            if repo and repo[-1] == '':
                repo.pop()
        res = {}
        for repo in repos:
            fp = self._findFP(repo)
            if fp is not None:
                res[fp.path] = repo
        return res
    
    def _find(self, segs, fsRepos):
        for fsRepo, repo in fsRepos.items():
            cand = os.path.join(fsRepo, *segs)
            if os.path.exists(cand):
                return FP(cand), '/'.join(['']+repo+segs)
        return None, None

    def _parse(self, data):
        for m in use_rx.finditer(data):
            yield eval('[' + m.group(1) + ']')[0]
        for m in require_rx.finditer(data):
            yield eval('[' + m.group(1) + ']')[0]                        
        for m in deps_rx.finditer(data):
            deps = eval(m.group(1))
            for d in deps:
                yield 'MochiKit.' + d

    def _parseDepsData(self, module, fp):
        mtime = fp.getmtime()
        try:
            old_mtime, depsData = self._depsData[module]
        except KeyError:
            old_mtime = -1
        if old_mtime != mtime:
            depsData = sorted(self._parse(fp.open().read()))
            self._depsData[module] = mtime, depsData
        return depsData

    def _simpleDeps(self, module, fsRepos, acc):
        fp = None
        if not module.startswith('/'):
            segs = module.split('.')
            segs[-1] = segs[-1] + '.js'
            thisFSRepos = fsRepos
        else:
            segs = module.split('/')[1:]
            for fsRepo, repo in fsRepos.items():
                if segs[:len(repo)] == repo:                  
                    thisFSRepos = {fsRepo: repo}
                    segs = segs[len(repo):]
                    break
            else:
                # xxx only for test running and tweb2 specific
                fp = self._findFP(segs)
                path = module

        if not fp:
            fp, path = self._find(segs, thisFSRepos)
            
        if fp is None:
            return None

        if path in acc:
            return path

        deps = []
        for dep in self._parseDepsData(module, fp):
            p = self._simpleDeps(dep, fsRepos, acc)
            if p:
                deps.append(p)

        acc[path] = deps
        return path

    def _fsRepos(self, repos):
        if repos is None:
            repos = self.defaultRepos
        fsRepos = self._findReposInFS(repos)
        return fsRepos

    def resolveHTML(self, html, repos=None):
        fsRepos = self._fsRepos(repos)

        params = {'jsResolver': self, 'fsRepos': fsRepos}
        return rewrite_html(html, HTMLResolver, params=params)

    def findDeps(self, module, repos=None):
        fsRepos = self._fsRepos(repos)        

        return self._findDeps(module, fsRepos)



class HTMLResolver(HTMLRewriter):

    def __init__(self, out, jsResolver, fsRepos=None):
        HTMLRewriter.__init__(self, out)
        self.injected = set()
        self.jsResolver = jsResolver
        self.fsRepos = fsRepos

    def inject_script(self, src):
        self.emit_start('script', {'src': src,
                                   'type': 'text/javascript'})
        self.emit_end('script')

    def rewrite_start(self, name, attrs):
        if name == 'meta':
            attrs = dict(attrs.items())
            if attrs.get('name') == 'oe:jsRepos':
                vals = attrs.get('content').split()
                self.fsRepos = self.jsResolver._findReposInFS(vals)
        elif name == 'script':
            attrs = dict(attrs.items())            
            src = attrs.get('src')
            if src and self.fsRepos is not None:
                injected = self.injected
                for dep in self.jsResolver._findDeps(src, self.fsRepos)[:-1]:
                    if dep not in injected:
                        self.inject_script(dep)
                        injected.add(dep)
 
        return False

# ________________________________________________________________
# twisted web2 stuff

class JsRoot(JsResolver):
    def __init__(self, webDir, jsDir):
        self.child_lib = static.File(webDir)
        self.child_js  = static.File(jsDir)        
        JsResolver.__init__(self)

    def _findFP(self, segs):
        cur = self
        curSegs = segs
        while cur:
            cur, curSegs = cur.locateChild(None, curSegs)
            if cur and curSegs == []:
                assert isinstance(cur, static.File)
                return cur.fp.path
        return None
