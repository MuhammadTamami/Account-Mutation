# Contributing to Bank Statement Converter

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- Bank type and file format (if applicable)
- Error messages or screenshots

### Suggesting Features

For feature requests, please create an issue with:
- Clear description of the feature
- Use case and why it's needed
- Example of how it would work

### Adding New Bank Support

To add support for a new bank:

1. **Create a processor** in `backend/processors/`:
   ```python
   # backend/processors/namabank_processor.py
   def process_namabank_pdf(filepath):
       # Your implementation
       pass
   ```

2. **Add detection patterns** in `backend/processors/bank_detector.py`:
   ```python
   # Add bank-specific patterns
   if 'nama bank' in text_lower:
       return 'NAMA_BANK'
   ```

3. **Add routing** in `backend/app.py`:
   ```python
   elif bank_name == 'NAMA_BANK':
       df = process_namabank_file(filepath, file_ext)
       file_type = f'Nama Bank {file_ext.upper()}'
   ```

4. **Test thoroughly** with multiple sample files

5. **Update documentation** in README.md

### Code Style

**Python:**
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions
- Handle errors gracefully

**JavaScript:**
- Use ES6+ features
- Use meaningful variable names
- Add comments for complex logic

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Create a Pull Request

### Testing

Before submitting a PR:
- Test with multiple sample files
- Verify accuracy of extracted data
- Check that existing features still work
- Test both single and batch upload

### Project Structure

```
BSI Excel Convert/
├── backend/           # Python Flask backend
│   ├── processors/    # Bank-specific processors
│   ├── uploads/       # Temporary uploads (gitignored)
│   └── outputs/       # Generated files (gitignored)
├── frontend/          # React frontend
│   └── src/
├── test_data/         # Test files (gitignored)
├── tests/             # Test scripts (gitignored)
└── docs/              # Documentation
    └── development/   # Dev docs (gitignored)
```

## Questions?

Feel free to create an issue for any questions or clarifications.

Thank you for contributing! 🎉
