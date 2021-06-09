class SC {
    static maxcnt = 3;
    key = null;
    cnt = 0;
    action = null;
    exclude = null;
    constructor(k, a, ex) { this.key = k; this.action = a; this.exclude = ex; }
    increment(c) { if ((c === undefined) || (c === this.key)) this.cnt++; else this.reset(); this.ready(); }
    ready() { if (this.cnt >= SC.maxcnt) { if (this.exclude && this.exclude.test(location.pathname)) return this.reset(); return this.action(); } }
    reset() { this.cnt = 0; }
}
let cj = {
    last: null,
    shortcuts: {
        'f': new SC('f', ()=>{location.pathname = `${location.pathname}/files`.replace(/\/\//g, '/')}, /files/),
    },
    register: () => { document.onkeydown = cj.trigger; },
    trigger: (e)=>{
        cj.last = e;
        for (var k in cj.shortcuts) cj.shortcuts[k].increment(e.key);
    },
};
