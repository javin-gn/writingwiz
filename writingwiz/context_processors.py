import time

# Computed once when the process starts, so it changes on every local restart
# and every fresh deployment - used as a cache-busting query string for static
# assets (see base.html) so browsers don't serve a stale cached stylesheet.
STATIC_VERSION = str(int(time.time()))


def static_version(request):
    return {'STATIC_VERSION': STATIC_VERSION}
