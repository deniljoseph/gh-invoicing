def post_fork(server, worker):
    # --preload runs app import in the master; threads don't survive fork, so start the scheduler per worker.
    import app as _a
    _a.start_backup_scheduler()
