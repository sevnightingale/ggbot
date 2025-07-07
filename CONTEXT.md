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
    font-size: 16px !important;
    padding: 12px 16px !important;
    transition: border-color 0.2s ease !important;
  }
  
  .launchlist-form input:focus {
    border-color: #38a1c7 !important;
    outline: none !important;
    box-shadow: 0 0 0 1px #38a1c7 !important;
  }
  
  .launchlist-form input::placeholder {
    color: #999999 !important;
  }
  
  .launchlist-form button {
    background: #38a1c7 !important;
    border: 2px solid #38a1c7 !important;
    color: #161618 !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    padding: 12px 24px !important;
    transition: all 0.2s ease !important;
    text-transform: none !important;
  }
  
  .launchlist-form button:hover {
    background: rgba(56, 161, 199, 0.8) !important;
    transform: translateY(-1px) !important;
  }
  
  /* Remove any default margins/padding */
  .launchlist-form {
    margin: 0 !important;
    padding: 0 !important;
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