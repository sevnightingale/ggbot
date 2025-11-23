93:6  Warning: React Hook useEffect has missing dependencies: 'configData', 'configId', and 'currentStrategy'. Either include them or remove the dependency array.  react-hooks/exhaustive-deps
info  - Need to disable some ESLint rules? Learn more here: https://nextjs.org/docs/app/api-reference/config/eslint#disabling-rules
Failed to compile.
./app/forge/components/monitor/ActivationBar.tsx:68:108
Type error: This comparison appears to be unintentional because the types '"paper" | undefined' and '"live"' have no overlap.
  66 |   const [riskModalOpen, setRiskModalOpen] = useState(false)
  67 |
> 68 |   const isLiveTrading = selectedBot.trading_mode === 'symphony' || selectedBot.trading_mode === 'aster' || selectedBot.trading_mode === 'live'
     |                                                                                                            ^
  69 |
  70 |   const handleActivate = () => {
  71 |     if (!canAccess('bot_activation')) {
Next.js build worker exited with code: 1 and signal: null
Error: Command "npm run build" exited with 1