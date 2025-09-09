Here’s the straight read, Sev: solid UX and lots of functionality, but there are a few **logic bugs**, **state-mutation risks**, and **DX/security** gaps that will bite you in prod.

# Verdict

Good scaffolding. Needs fixes before you trust it with user configs and API keys.

## Blockers / Bugs

* **Selection by name (not ID) = incorrect toggles & key collisions.**
  You store selected data points by **name** and render chips keyed by `dataPointName`. If two sources share a name, removing a chip may toggle the wrong point, and React keys will collide. Store selections as `{source, id}` and render keys as `${source}:${id}`.
* **Shallow “immutable” update mutates nested objects.**
  `newConfig = { ...prev }` then mutating `newConfig.extraction.selected_data_sources[category]` mutates nested references from `prev`. It works by chance (top-level object changes) but breaks memoization and can introduce heisenbugs. Use an immutable update (Immer) or deep-clone only the branch you change.
* **Race/leak on async init.**
  `initializeComponent()` doesn’t cancel if the sheet closes mid-flight. You also don’t clear the open/close timeouts. Both can set state after unmount.
* **Default numeric values use `||` instead of `??`.**
  `value={x || 100}` treats `0` as falsy; 0% is legitimate in some fields. Use `??` + explicit min validation.
* **Variable shadowing.**
  In `selectedDataPoints` memo you create `const dataSources = configData.extraction.selected_data_sources`, shadowing the `dataSources` state (array). This is confusing and error-prone; rename to `selectedSources`.
* **Reset naming inconsistency.**
  New bot name toggles between **“New ggbot”** and **“New Bot”**. Pick one.
* **“alert” in 2025 UX.**
  `alert('Signal Validation requires an upgraded plan')` is a jarring blocking UI; you already have patterns for inline gates.

## Risky Patterns / Security

* **API keys in a shared input state.**
  One `credentialInput` for all providers = accidental reuse/leak across tabs. Use provider-scoped state or clear on provider change. Never log credential operations.
* **Console logging sensitive payloads.**
  You `console.log` API responses and errors broadly; these often include user data. Strip before prod.

## Performance

* **O(n²) chip render lookups.**
  Each chip does a `.flatMap(...).find(...)`. Build a `Map<data_point_id -> DataPoint>` once via `useMemo`.
* **Potentially large lists.**
  Pairs and data points should be **virtualized** (e.g., `react-window`) to keep scroll silky.

## Accessibility & UX

* **Modal/bottom sheet should be a real dialog.**
  Add `role="dialog" aria-modal="true"`, label it, trap focus, close on `Esc`.
* **Dropdown should be a combobox/listbox.**
  Current click-out handler is fine, but use a `ref`+containment (not `document.querySelector`/`closest` strings) and add keyboard navigation.
* **Buttons need aria-labels.**
  Icon-only buttons (save/reset/exit/chips) should have `aria-label`.

## High-impact fixes (snippets)

### 1) Immutable nested updates (Immer)

```ts
import { produce } from 'immer';

const updateConfigData = (updater: (draft: ConfigData) => void) => {
  setConfigData(prev => produce(prev, draft => { updater(draft) }));
  setHasChanges(true);
};

// Example: toggle data point by {source, id}
updateConfigData(d => {
  const sel = d.extraction.selected_data_sources;
  const category = sourceInfo.name as keyof typeof sel;

  sel[category] ??= { data_points: [], timeframes: ["5m","15m","30m","1h","4h","1d","1w"] };
  const dpKey = `${category}:${dataPoint.data_point_id}`;

  const arr = sel[category]!.data_points as string[]; // now store KEYS, not names
  const idx = arr.indexOf(dpKey);
  if (idx >= 0) arr.splice(idx, 1); else arr.push(dpKey);
});
```

### 2) Store/render by **unique key**, not name

```ts
// Build a quick index
const dpIndex = React.useMemo(() => {
  const map = new Map<string, DataPoint & { source: string }>();
  for (const s of dataSources)
    for (const dp of s.data_points)
      map.set(`${s.name}:${dp.data_point_id}`, { ...dp, source: s.name });
  return map;
}, [dataSources]);

// Selected chip render (unique key + safe removal)
{selectedDataPoints.map(dpKey => {
  const dp = dpIndex.get(dpKey);
  if (!dp) return null;
  return (
    <span key={dpKey} /* ... */>
      {dp.name}
      <button onClick={() => handleToggleDataPoint(dp.data_point_id, dp.source)} aria-label={`Remove ${dp.name}`}>
        …
      </button>
    </span>
  );
})}
```

### 3) Cancel async init + clear timeouts

```ts
React.useEffect(() => {
  if (!isOpen) return;
  let cancelled = false;
  const tShow = setTimeout(() => setIsVisible(true), 50);

  (async () => {
    try {
      setIsLoading(true); setError(null);
      const [ds, profile, creds] = await Promise.all([
        apiClient.getDataSourcesWithPoints(),
        apiClient.getUserProfile(),
        apiClient.listCredentials()
      ]);
      if (cancelled) return;
      setDataSources(ds); setUserProfile(profile); setUserCredentials(creds);
      // ...
    } catch (e) {
      if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load configuration');
    } finally {
      if (!cancelled) { setIsLoading(false); setDataSourcesLoading(false); }
    }
  })();

  return () => { cancelled = true; clearTimeout(tShow); };
}, [isOpen, bot?.config_id]);
```

### 4) Replace `||` with `??` for numeric inputs

```tsx
value={configData.trading.position_sizing.fixed_amount_usd ?? 100}
```

### 5) Safer outside-click with ref

```ts
const dropdownRef = React.useRef<HTMLDivElement>(null);
React.useEffect(() => {
  if (!showPairDropdown) return;
  const onDown = (e: MouseEvent) => {
    if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
      setShowPairDropdown(false); setPairSearchTerm('');
    }
  };
  document.addEventListener('mousedown', onDown);
  return () => document.removeEventListener('mousedown', onDown);
}, [showPairDropdown]);
```

### 6) Dialog a11y

```tsx
<div role="dialog" aria-modal="true" aria-labelledby="ggbot-config-title" className="fixed inset-0 …">
  …
  <h2 id="ggbot-config-title"> {botName} </h2>
</div>
```

### 7) Virtualize long lists

Swap the mapped lists for `react-window` (`FixedSizeList`) to keep memory/paint costs down.

## Smaller polish

* Add `onKeyDown` handlers for Enter/Escape in inputs and menus.
* Inline “upgrade required” instead of `alert`.
* Clear `credentialInput` on provider switch; show per-provider controlled inputs.
* Remove broad `console.log` in production builds.

---

If you fix the **ID-vs-name selection**, **immutability**, and **async cleanup**, you’ll eliminate 80% of the risk. Add a11y and virtualization for finish-quality.
