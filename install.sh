echo "🏛️  MemBridge - Termux Memory Palace Installer"
echo "==============================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📦 Downloading MemBridge...${NC}"

# Create directory
mkdir -p ~/.membridge
cd ~/.membridge

# Download the bridge script
curl -sSL https://raw.githubusercontent.com/yusdesign/membridge/main/mempalace-bridge.py -o mempalace-bridge.py

# Make executable
chmod +x mempalace-bridge.py

# Create alias
if ! grep -q "alias membridge=" ~/.bashrc; then
    echo "alias membridge='python ~/.membridge/mempalace-bridge.py'" >> ~/.bashrc
fi

# Initial setup
echo -e "${BLUE}⚙️  Initializing database...${NC}"
python mempalace-bridge.py status > /dev/null 2>&1

echo ""
echo -e "${GREEN}✅ MemBridge installed successfully!${NC}"
echo ""
echo "Quick start:"
echo "  source ~/.bashrc          # Reload aliases"
echo "  membridge mine            # Index your Termux home"
echo "  membridge search 'query'  # Search memories"
echo "  membridge wake-up         # Get context for AI"
echo ""
echo -e "${BLUE}☘️  Happy coding! ☘️${NC}"
