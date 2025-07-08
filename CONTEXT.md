# LaunchList Custom Head Code

Copy and paste this into the "Head Code" section of LaunchList:

```html
<style>
  /* Brutalist styling overrides */
  .launchlist-form * {
    border-radius: 0 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  }
  
  .launchlist-form input {
    border: 2px solid #e3e5e6 !important;
    background: #161618 !important;
    color: #e3e5e6 !important;
    font-size: 15px !important;
    padding: 14px 16px !important;
    transition: border-color 0.2s ease !important;
    line-height: 1.4 !important;
    /* Mobile improvements */
    -webkit-appearance: none !important;
    -moz-appearance: none !important;
    appearance: none !important;
    touch-action: manipulation !important;
  }
  
  .launchlist-form input:focus {
    border-color: #38a1c7 !important;
    outline: none !important;
    box-shadow: 0 0 0 1px #38a1c7 !important;
  }
  
  .launchlist-form input::placeholder {
    color: #999999 !important;
    font-size: 15px !important;
  }
  
  .launchlist-form button {
    background: #38a1c7 !important;
    border: 2px solid #38a1c7 !important;
    color: #161618 !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 14px 28px !important;
    transition: all 0.2s ease !important;
    text-transform: none !important;
    letter-spacing: 0.025em !important;
    /* Mobile touch improvements */
    -webkit-appearance: none !important;
    -moz-appearance: none !important;
    appearance: none !important;
    touch-action: manipulation !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    -webkit-tap-highlight-color: transparent !important;
  }
  
  .launchlist-form button:hover {
    background: rgba(56, 161, 199, 0.8) !important;
    transform: translateY(-1px) !important;
  }
  
  /* Mobile-specific button styling */
  @media (max-width: 768px) {
    .launchlist-form button {
      padding: 16px 32px !important;
      font-size: 16px !important;
      min-height: 48px !important;
    }
    
    .launchlist-form input {
      font-size: 16px !important;
      min-height: 48px !important;
    }
  }
  
  /* Remove any default margins/padding and adjust spacing */
  .launchlist-form {
    margin: 0 !important;
    padding: 0 !important;
  }
  
  /* Ensure consistent spacing in the form */
  .launchlist-form > div {
    margin-bottom: 12px !important;
  }
  
  .launchlist-form > div:last-child {
    margin-bottom: 0 !important;
  }
  
  /* Prevent double-tap zoom on mobile */
  .launchlist-form * {
    touch-action: manipulation !important;
  }
</style>
```

## Settings Summary for LaunchList:

- **Rounded corner**: 0px
- **Form position**: Center  
- **Items alignment**: Stack
- **Font Size**: 16px
- **Border Width**: 2px
- **Email placeholder**: "Enter your email address"
- **Collect name**: Disabled
- **Input Border Color**: #e3e5e6
- **Input Background Color**: #161618
- **Input Text Color**: #e3e5e6
- **Input Placeholder Color**: #999999
- **Button Text**: "Join Waitlist"
- **Button Color**: #38a1c7
- **Button Border Color**: #38a1c7
- **Button Text Color**: #161618