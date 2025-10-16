# Wolfinch Installation Guide

Complete installation guide for Wolfinch with PaperTrader for NSE trading.

## 🚀 Quick Install (Recommended)

### Option 1: Automated Setup Script

```bash
# Run the setup script
./setup_venv.sh

# Activate virtual environment
source venv/bin/activate

# You're ready to go!
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip setuptools wheel

# 4. Install dependencies
pip install -r requirement.txt

# 5. Run Wolfinch
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

## 📋 Prerequisites

### System Requirements

- **OS**: Linux, macOS, or Windows (WSL recommended)
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 500MB for installation + space for data

### Required System Packages

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-dev build-essential
```

#### Fedora/RHEL
```bash
sudo dnf install python3 python3-virtualenv python3-pip python3-devel gcc
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3
```

## 🔧 Detailed Installation Steps

### Step 1: Clone or Download Wolfinch

If you haven't already:
```bash
cd ~/Projects
git clone <wolfinch-repo-url>
cd wolfinch
```

### Step 2: Install Python Dependencies

#### Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirement.txt
```

#### Without Virtual Environment (Not Recommended)

```bash
# Only if you can't use venv
pip install --user -r requirement.txt
```

### Step 3: Verify Installation

```bash
# Check if all packages are installed
pip list

# Should see packages like:
# deap, Flask, numpy, tulipy, etc.
```

### Step 4: Setup Data Directory

```bash
# Create raw_data directory
mkdir -p raw_data

# Copy sample data
cp raw_data_sample/BANK_minute.csv raw_data/
```

### Step 5: Test Run

```bash
# Run with sample config
./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml
```

## 🐛 Troubleshooting

### Issue 1: `deap` Installation Error

**Error**: `use_2to3 is invalid`

**Solution**: The `requirement.txt` has been updated to use `deap>=1.4.1`. If you still see this error:

```bash
pip install deap>=1.4.1 --upgrade
```

### Issue 2: `tulipy` Installation Error

**Error**: `error: command 'gcc' failed`

**Solution**: Install build tools

```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev

# Fedora/RHEL
sudo dnf install gcc python3-devel

# macOS
xcode-select --install
```

### Issue 3: Externally Managed Environment

**Error**: `externally-managed-environment`

**Solution**: Use virtual environment (see Step 2 above)

### Issue 4: Permission Denied

**Error**: `Permission denied: './Wolfinch.py'`

**Solution**: Make script executable

```bash
chmod +x Wolfinch.py
```

### Issue 5: Module Not Found

**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**: Ensure virtual environment is activated

```bash
source venv/bin/activate
pip install -r requirement.txt
```

### Issue 6: Port Already in Use

**Error**: `Address already in use: 8080`

**Solution**: Change port in config or kill existing process

```bash
# Change port in config
# ui:
#   port: 8081

# OR kill process using port 8080
lsof -ti:8080 | xargs kill -9
```

## 📦 Package Details

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `deap` | >=1.4.1 | Genetic algorithm optimizer |
| `Flask` | >=1.1.2 | Web UI |
| `numpy` | >=1.18.5 | Numerical computations |
| `tulipy` | >=0.4.0 | Technical indicators |
| `SQLAlchemy` | >=1.3.17 | Database ORM |
| `PyYAML` | >=5.3.1 | Config file parsing |

### Optional Dependencies

For live trading (not needed for PaperTrader):
- `websocket-client` - WebSocket connections
- `requests` - HTTP requests
- `gevent` - Async operations

## 🔄 Updating Wolfinch

```bash
# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirement.txt --upgrade

# Or update specific package
pip install deap --upgrade
```

## 🧹 Uninstallation

```bash
# Remove virtual environment
rm -rf venv

# Remove data (optional)
rm -rf raw_data

# Remove database (optional)
rm -rf db/*.db
```

## 💻 Development Setup

For development work:

```bash
# Install development dependencies
pip install pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black .

# Lint code
flake8 .
```

## 🐳 Docker Installation (Alternative)

If you prefer Docker:

```bash
# Build Docker image
docker build -t wolfinch .

# Run container
docker run -p 8080:8080 -v $(pwd)/raw_data:/app/raw_data wolfinch
```

## 🌐 Virtual Environment Tips

### Activating Virtual Environment

```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# You should see (venv) in your prompt
```

### Deactivating Virtual Environment

```bash
deactivate
```

### Checking Active Environment

```bash
which python
# Should show: /path/to/wolfinch/venv/bin/python
```

## 📝 Post-Installation Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list`)
- [ ] `raw_data/` directory created
- [ ] Sample CSV files copied to `raw_data/`
- [ ] Config files reviewed
- [ ] Test run successful
- [ ] UI accessible at `http://localhost:8080`

## 🎯 Next Steps

After successful installation:

1. **Generate Data**: Run `python3 raw_data_sample/generate_nse_data.py`
2. **Copy Data**: `cp raw_data_sample/*.csv raw_data/`
3. **Configure**: Edit `config/wolfinch_papertrader_nse_banknifty.yml`
4. **Run**: `./Wolfinch.py --config config/wolfinch_papertrader_nse_banknifty.yml`
5. **Access UI**: Open `http://localhost:8080` in browser

## 📚 Additional Resources

- **Main README**: `README.md`
- **PaperTrader Guide**: `PAPERTRADER_QUICKSTART.md`
- **NSE Trading**: `NSE_TRADING_GUIDE.md` (if exists)
- **Multi-Stock**: `MULTI_STOCK_TRADING.md`

## 🆘 Getting Help

If you encounter issues:

1. Check this troubleshooting section
2. Review error messages carefully
3. Ensure all prerequisites are met
4. Check Python and package versions
5. Try in a fresh virtual environment

## ✅ Verification Commands

```bash
# Check Python version
python3 --version

# Check pip version
pip --version

# Check installed packages
pip list

# Check if Wolfinch can import modules
python3 -c "import numpy, tulipy, yaml; print('OK')"

# Check if config is valid
python3 -c "import yaml; yaml.safe_load(open('config/papertrader.yml'))"
```

Happy trading! 🚀
