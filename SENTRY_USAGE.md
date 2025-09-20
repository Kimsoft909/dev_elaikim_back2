# Sentry Error Tracking Usage Guide

## What is Sentry?

Sentry is already configured in the Django backend for production error tracking and performance monitoring. Here's how to use it effectively:

## Configuration

1. **Environment Variable**: Set `SENTRY_DSN` in your production environment:
   ```bash
   SENTRY_DSN=https://your-dsn@o123456.ingest.sentry.io/123456
   ```

2. **Environment Detection**: The system automatically detects production vs development using the `ENVIRONMENT` variable.

## Automatic Error Capture

Sentry automatically captures:

- **Unhandled exceptions** in views and middleware
- **Database errors** and connection issues  
- **Performance issues** with slow database queries
- **Celery task failures** (background jobs)
- **HTTP 5xx errors** from the API

## Manual Error Tracking

You can manually capture errors in your code:

```python
import sentry_sdk
from sentry_sdk import capture_exception, capture_message

try:
    # Your code that might fail
    risky_operation()
except Exception as e:
    # Capture with full context
    capture_exception(e)
    
# Or capture custom messages
capture_message("Something important happened", level="warning")
```

## Adding Context

Add user context to errors:

```python
from sentry_sdk import set_user, set_tag, set_context

# Set user information
set_user({"id": user.id, "email": user.email})

# Add custom tags
set_tag("component", "authentication")

# Add custom context
set_context("request_info", {
    "url": request.path,
    "method": request.method,
    "user_agent": request.META.get('HTTP_USER_AGENT')
})
```

## Performance Monitoring

Sentry tracks:

- **API response times** automatically
- **Database query performance**
- **Cache hit/miss rates**
- **External API calls** (Supabase, etc.)

## Production Setup Steps

1. **Create Sentry Project**: Go to [sentry.io](https://sentry.io) and create a new Django project
2. **Get DSN**: Copy your project's DSN from Settings > Client Keys
3. **Set Environment Variable**: Add `SENTRY_DSN=your_dsn_here` to your production environment
4. **Deploy**: Sentry will automatically start capturing errors

## Dashboard Features

In your Sentry dashboard, you can:

- **View error trends** and frequency
- **Get email/Slack alerts** for new errors
- **See performance bottlenecks** in your API
- **Track releases** and error rates per deployment
- **Debug with full stack traces** and request context

## Sample Rate Configuration

The current configuration captures:
- **10% of performance data** (`traces_sample_rate=0.1`)
- **100% of errors** (all errors are captured)
- **User context** (`send_default_pii=True`) for better debugging

## Best Practices

1. **Don't log sensitive data**: Avoid logging passwords, tokens, or PII
2. **Use appropriate levels**: Use `warning` for expected issues, `error` for failures
3. **Add meaningful context**: Include relevant business context with errors
4. **Monitor release performance**: Track error rates after deployments
5. **Set up alerts**: Configure notifications for critical errors

## Testing Sentry

To test if Sentry is working:

```python
# In Django shell or a test view
import sentry_sdk
sentry_sdk.capture_message("Testing Sentry integration", level="info")
```

This should appear in your Sentry dashboard within a few seconds.