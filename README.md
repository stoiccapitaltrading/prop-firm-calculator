# prop-firm-calculator

A Streamlit app for prop firm traders with:
- **Payout Calculator** (main page)
- **Risk of Ruin Calculator** for a prop firm rule model (daily + overall drawdown)

## Block merge-conflict markers from commits
Unresolved markers like `<<<<<<<`, `=======`, `>>>>>>>` should never be committed.

### One-time setup
```bash
./scripts/install_git_hooks.sh
```

### Manual check (optional)
```bash
./scripts/check_conflict_markers.sh
```

After setup, the pre-commit hook runs automatically and rejects commits that contain conflict markers.

### CI protection
A GitHub Actions workflow also runs this check on every PR/push and fails if conflict markers are present.
