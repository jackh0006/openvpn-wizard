# Contributing to OpenVPN Wizard

We welcome all contributions! Whether you're fixing a typo, adding a feature, or improving documentation, your help makes this project better for everyone.

## How to Contribute

### 1. Fork the Repository
Go to https://github.com/jackh0006/OpenVPN-Wizard and click "Fork".

### 2. Clone Your Fork
```bash
git clone https://github.com/YOUR_USERNAME/OpenVPN-Wizard.git
cd OpenVPN-Wizard
```

### 3. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes
- Follow the code style guidelines below
- Add tests for new functionality
- Update documentation if user-facing
- Run the validation checklist after changes

### 5. Commit Your Changes
```bash
git add .
git commit -m "feat: description of your change"
```

**Commit message format:**
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

### 6. Push and Open a Pull Request
```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

## Code Style

### Python
- Python 3.11+
- Type hints on all functions
- Black formatting (100 char line length)
- Ruff for linting
- MyPy for type checking
- Rich for all terminal output

### Documentation
- Explain like talking to a 5-year-old (without saying it)
- Use tables for comparisons
- Include analogies for complex concepts
- Show what each entity sees/doesn't see
- Provide step-by-step instructions

### Shell Scripts
- Use `set -euo pipefail`
- Comment complex logic
- Check for errors

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=installer

# Run specific test
pytest tests/test_specific.py
```

## Documentation Standards

All user-facing documentation must:
1. Use simple language (no unnecessary jargon)
2. Include examples
3. Show what to expect at each step
4. Have a troubleshooting section
5. Be tested by someone who hasn't seen it before

## Review Process

1. All pull requests are reviewed by at least one maintainer
2. Changes must pass CI checks
3. Documentation changes must be reviewed for clarity
4. Security changes require extra review

## Attribution

All contributors are credited in CONTRIBUTORS.md.

## Questions?

Open a GitHub issue or email jackh109867@gmail.com.