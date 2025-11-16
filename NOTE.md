            let {positions: t=[], className: a="", selectedConfigId: n, onPositionClosed: i} = e
              , [o,c] = (0,
            s.useState)({})
              , [d,m] = (0,
            s.useState)({})
              , x = (0,
            s.useRef)({})
              , [u,g] = (0,
            s.useState)({})
              , h = e => {
                if (e >= 1e4 || e >= 1e3)
                    return "$".concat(e.toLocaleString(void 0, {
                        maximumFractionDigits: 2
                    }));
                if (e >= 100)
                    return "$".concat(e.toFixed(2));
                if (e >= 1)
                    return "$".concat(e.toFixed(4));
                if (e >= .01)
                    return "$".concat(e.toFixed(6));
                else if (e >= 1e-4)
                    return "$".concat(e.toFixed(8));
                else
                    return "$".concat(e.toFixed(10))
            }
              , p = e => {
                let t = e >= 0 ? "+" : "";
                return "".concat(t, "$").concat(e.toFixed(2))
            }
              , v = (e, t) => {
                let a = (t - e) / e * 100
                  , r = a >= 0 ? "+" : "";
               