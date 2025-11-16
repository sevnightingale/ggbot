Content Security Policy of your site blocks the use of 'eval' in JavaScript`
The Content Security Policy (CSP) prevents the evaluation of arbitrary strings as JavaScript to make it more difficult for an attacker to inject unathorized code on your site.

To solve this issue, avoid using eval(), new Function(), setTimeout([string], ...) and setInterval([string], ...) for evaluating strings.

If you absolutely must: you can enable string evaluation by adding unsafe-eval as an allowed source in a script-src directive.

⚠️ Allowing string evaluation comes at the risk of inline script injection.

1 directive
Source location	Directive	Status
script-src	blocked



page-20cee6f459983eae.js:1 Uncaught TypeError: Cannot read properties of null (reading 'toFixed')
    at h (page-20cee6f459983eae.js:1:55450)
    at page-20cee6f459983eae.js:1:60916
    at Array.map (<anonymous>)
    at eg (page-20cee6f459983eae.js:1:59943)
    at l2 (4bd1b696-143fc5c1a7e46772.js:1:50093)
    at ox (4bd1b696-143fc5c1a7e46772.js:1:69884)
    at oU (4bd1b696-143fc5c1a7e46772.js:1:81079)
    at ic (4bd1b696-143fc5c1a7e46772.js:1:112384)
    at 4bd1b696-143fc5c1a7e46772.js:1:112229
    at is (4bd1b696-143fc5c1a7e46772.js:1:112237)
    at u5 (4bd1b696-143fc5c1a7e46772.js:1:109320)
    at iH (4bd1b696-143fc5c1a7e46772.js:1:129977)
    at MessagePort.w (684-96a35eafa40ce8c6.js:1:25957)
h	@	page-20cee6f459983eae.js:1
(anonymous)	@	page-20cee6f459983eae.js:1
eg	@	page-20cee6f459983eae.js:1
l2	@	4bd1b696-143fc5c1a7e46772.js:1
ox	@	4bd1b696-143fc5c1a7e46772.js:1
oU	@	4bd1b696-143fc5c1a7e46772.js:1
ic	@	4bd1b696-143fc5c1a7e46772.js:1
(anonymous)	@	4bd1b696-143fc5c1a7e46772.js:1
is	@	4bd1b696-143fc5c1a7e46772.js:1
u5	@	4bd1b696-143fc5c1a7e46772.js:1
iH	@	4bd1b696-143fc5c1a7e46772.js:1
w	@	684-96a35eafa40ce8c6.js:1




🛑 Cleaning up SSE connection
page-20cee6f459983eae.js:1 API responses: {balanceOk: true, balanceStatus: 200, activitiesOk: true, activitiesStatus: 200, metadataOk: true, …}activitiesOk: trueactivitiesStatus: 200balanceOk: truebalanceStatus: 200metadataOk: truemetadataStatus: 200[[Prototype]]: Objectconstructor: ƒ Object()hasOwnProperty: ƒ hasOwnProperty()isPrototypeOf: ƒ isPrototypeOf()propertyIsEnumerable: ƒ propertyIsEnumerable()toLocaleString: ƒ toLocaleString()toString: ƒ toString()valueOf: ƒ valueOf()__defineGetter__: ƒ __defineGetter__()__defineSetter__: ƒ __defineSetter__()__lookupGetter__: ƒ __lookupGetter__()__lookupSetter__: ƒ __lookupSetter__()__proto__: (...)get __proto__: ƒ __proto__()set __proto__: ƒ __proto__()
page-20cee6f459983eae.js:1 Raw balance points: 3
page-20cee6f459983eae.js:1 Raw activities: 2
page-20cee6f459983eae.js:1 Chart data points (snapshots + activities): 3
page-20cee6f459983eae.js:1 Final chart data: 3 points
page-20cee6f459983eae.js:1 First 3 points: (3) [{…}, {…}, {…}]0: {time: 1763253493, value: 0}1: {time: 1763253572, value: 0}2: {time: 1763253589, value: 0}length: 3[[Prototype]]: Array(0)
page-20cee6f459983eae.js:1 Last 3 points: (3) [{…}, {…}, {…}]0: {time: 1763253493, value: 0}1: {time: 1763253572, value: 0}2: {time: 1763253589, value: 0}length: 3[[Prototype]]: Array(0)
page-20cee6f459983eae.js:1 Time spacing (first 3 points):
page-20cee6f459983eae.js:1   Point 0 to 1: 79 seconds (0.021944444444444444 hours)
page-20cee6f459983eae.js:1   Point 1 to 2: 17 seconds (0.004722222222222222 hours)
page-20cee6f459983eae.js:1   Point 0 date: 2025-11-16T00:38:13.000Z
page-20cee6f459983eae.js:1   Point 1 date: 2025-11-16T00:39:32.000Z
page-20cee6f459983eae.js:1 Line series ref exists: false
page-20cee6f459983eae.js:1 Cannot set data: {hasLineSeries: false, dataLength: 3}dataLength: 3hasLineSeries: false[[Prototype]]: Objectconstructor: ƒ Object()hasOwnProperty: ƒ hasOwnProperty()isPrototypeOf: ƒ isPrototypeOf()propertyIsEnumerable: ƒ propertyIsEnumerable()toLocaleString: ƒ toLocaleString()toString: ƒ toString()valueOf: ƒ valueOf()__defineGetter__: ƒ __defineGetter__()__defineSetter__: ƒ __defineSetter__()__lookupGetter__: ƒ __lookupGetter__()__lookupSetter__: ƒ __lookupSetter__()__proto__: (...)get __proto__: ƒ __proto__()set __proto__: ƒ __proto__()