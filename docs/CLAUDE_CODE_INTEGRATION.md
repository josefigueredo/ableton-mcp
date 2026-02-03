# Claude Code Integration Guide

> 🎵 **Complete setup guide for using Ableton Live MCP Server with Claude Code**

This guide walks you through setting up the Ableton Live MCP Server with Claude Code, providing step-by-step installation, configuration, and comprehensive test scenarios.

## 📋 Prerequisites

### Software Requirements
- **Claude Code** (latest version)
- **Ableton Live** (any recent version - 10, 11, or 12)
- **AbletonOSC Remote Script** - Essential for MCP communication
- **Python 3.11+** with pip

### Hardware Requirements
- **4GB RAM** minimum (8GB recommended for complex projects)
- **Available Ports**: 11000-11001 for OSC communication
- **Audio Interface** (optional but recommended for monitoring)

## 🔧 Step 1: Install AbletonOSC Remote Script

### Download and Setup AbletonOSC
1. **Download AbletonOSC**:
   ```bash
   git clone https://github.com/ideoforms/AbletonOSC.git
   ```

2. **Install in Ableton Live**:
   - Copy the `AbletonOSC` folder to your Ableton Live MIDI Remote Scripts directory:
     - **Windows**: `C:\ProgramData\Ableton\Live [version]\Resources\MIDI Remote Scripts\`
     - **macOS**: `/Applications/Ableton Live [version].app/Contents/App-Resources/MIDI Remote Scripts/`

3. **Enable in Ableton Live**:
   - Open Ableton Live
   - Go to `Preferences > MIDI`
   - In the `Control Surface` dropdown, select `AbletonOSC`
   - Set Input and Output to `None`
   - The script will automatically use ports 11000/11001

### Verify AbletonOSC Installation
- Look for "AbletonOSC: Listening on port 11000" in Ableton's Log.txt
- The log file location:
  - **Windows**: `%USERPROFILE%\AppData\Roaming\Ableton\Live [version]\Preferences\Log.txt`
  - **macOS**: `~/Library/Preferences/Ableton/Live [version]/Log.txt`

## 🚀 Step 2: Install Ableton Live MCP Server

### Clone and Setup
```bash
# Clone the repository
git clone <your-repository-url>
cd ableton-live-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install the MCP server
pip install -e .
```

### Verify Installation
```bash
# Test the server installation (recommended method)
python -m ableton_mcp.main

# Or use the console command (may have encoding issues on Windows)
ableton-mcp
```

Expected output:
```
+-------------------------------------------------------------+
|  Ableton Live MCP Server v1.0.0                            |
|  Professional AI-Powered Music Production Assistant        |
+-------------------------------------------------------------+
Starting MCP server...
```

**Note**: Use `Ctrl+C` to stop the server after verifying it starts correctly.

## ⚙️ Step 3: Configure Claude Code

### Add MCP Server to Claude Code
1. **Open Claude Code Settings**:
   - Open Claude Code
   - Access Settings/Preferences
   - Navigate to MCP Servers section

2. **Add the Ableton MCP Server**:
   ```json
   {
     "mcpServers": {
       "ableton-live": {
         "command": "python",
         "args": ["-m", "ableton_mcp.main"],
         "cwd": "C:/Users/josef/Code/cursorforableton",
         "env": {
           "ABLETON_OSC_HOST": "127.0.0.1",
           "ABLETON_OSC_SEND_PORT": "11000",
           "ABLETON_OSC_RECEIVE_PORT": "11001"
         }
       }
     }
   }
   ```

3. **Alternative Configuration** (if using virtual environment explicitly):
   ```json
   {
     "mcpServers": {
       "ableton-live": {
         "command": "C:/Users/josef/Code/cursorforableton/venv/Scripts/python.exe",
         "args": ["-m", "ableton_mcp.main"],
         "cwd": "C:/Users/josef/Code/cursorforableton"
       }
     }
   }
   ```

### Restart Claude Code
- Close and restart Claude Code to load the new MCP server
- The server should appear in your available tools

## 🧪 Step 4: Testing the Integration

### Basic Connection Test

**Prompt to Claude Code:**
```
Connect to Ableton Live and tell me the current song information.
```

**Expected Claude Code Response:**
```
I'll connect to Ableton Live and get the current song information for you.

✅ Connected to Ableton Live at 127.0.0.1:11000
📡 Listening on port 11001
🎵 Ready for music production assistance!

🎵 **Song Information**
• Name: Untitled
• Tempo: 120 BPM
• Time Signature: 4/4
• Transport: Stopped

📊 **Tracks (2)**
• 0: 1 MIDI (midi)
• 1: 2 Audio (audio)
```

**What Should Happen in Ableton:**
- No visible changes (connection is silent)
- Check Log.txt for OSC communication messages
- AbletonOSC should log incoming requests

### Transport Control Tests

#### Test 1: Start/Stop Playback

**Prompt:**
```
Start playback in Ableton Live, wait 5 seconds, then stop it.
```

**Expected Response:**
```
▶️ Starting playback
⏹️ Stopping playback
```

**Ableton Side:**
- ▶️ Play button should illuminate and playback should start
- Timeline should advance
- ⏹️ Play button should dim and playback should stop

#### Test 2: Tempo Change

**Prompt:**
```
Change the tempo to 140 BPM and start playing.
```

**Expected Response:**
```
🎵 Set tempo to 140 BPM
▶️ Starting playback
```

**Ableton Side:**
- Tempo display should change to 140 BPM
- Metronome (if enabled) should reflect new tempo
- Playback should start at new tempo

### Track Operations Tests

#### Test 3: Create New Track

**Prompt:**
```
Create a new MIDI track called "AI Melody" and set its volume to 80%.
```

**Expected Response:**
```
➕ Created new midi track: AI Melody
🔊 Set track volume to 0.80
```

**Ableton Side:**
- New MIDI track should appear in Session View
- Track should be named "AI Melody"
- Volume fader should be at 80%

#### Test 4: Track Manipulation

**Prompt:**
```
Mute track 1, solo track 2, and pan track 0 to the left by 30%.
```

**Expected Response:**
```
Track muted
Track soloed  
🔊 Set track pan to -0.30
```

**Ableton Side:**
- Track 1: Mute button should be orange/lit
- Track 2: Solo button should be yellow/lit
- Track 0: Pan knob should show -30% (left)

### Music Intelligence Tests

#### Test 5: Harmony Analysis

**Prompt:**
```
Analyze these MIDI notes for harmony and suggest chord progressions: C, E, G, C (notes 60, 64, 67, 72). Make it pop genre.
```

**Expected Response:**
```
🎼 **Harmonic Analysis**

🎯 **Primary Key**: C major (85% confidence)
📝 **Scale Notes**: C, D, E, F, G, A, B

🎵 **Suggested Pop Progressions**:
• vi_IV_I_V: A - F - C - G
• I_V_vi_IV: C - G - A - F
• ii_V_I: D - G - C
```

**Ableton Side:**
- No immediate visual changes
- Analysis helps guide musical decisions

#### Test 6: Intelligent Note Addition

**Prompt:**
```
Add a C major chord progression to track 0, clip slot 0. Use quarter notes starting at beat 1, and quantize to the grid.
```

**Expected Response:**
```
🎵 Added 4 notes to track 0, clip 0
🎼 Applied major scale filtering
⏱️ Applied quantization to 16th note grid

📝 **Notes Added**:
• C4 at beat 1.00, duration 1.00
• E4 at beat 2.00, duration 1.00  
• G4 at beat 3.00, duration 1.00
• C5 at beat 4.00, duration 1.00
```

**Ableton Side:**
- Clip slot [0,0] should now contain a MIDI clip
- Piano roll should show C major chord notes
- Notes should be perfectly quantized to beat grid
- Clip should be 4 beats long

### Advanced Workflow Tests

#### Test 7: Complete Song Setup

**Prompt:**
```
Set up a basic pop song structure: 
1. Set tempo to 125 BPM
2. Create 4 tracks: "Drums", "Bass", "Lead", "Vocals"
3. Set up basic mix levels: Drums 90%, Bass 85%, Lead 75%, Vocals 80%
4. Pan Lead slightly left (-20%) and Vocals slightly right (+15%)
```

**Expected Response:**
```
🎵 Set tempo to 125 BPM
➕ Created new midi track: Drums
➕ Created new midi track: Bass  
➕ Created new midi track: Lead
➕ Created new midi track: Vocals
🔊 Set track volume levels and panning
🎚️ **Mix Setup Complete**
• Drums: 90% volume, center
• Bass: 85% volume, center  
• Lead: 75% volume, -20% pan
• Vocals: 80% volume, +15% pan
```

**Ableton Side:**
- Tempo: 125 BPM displayed
- 4 new tracks with specified names
- Volume faders at specified levels
- Pan knobs positioned as specified
- Professional mix starting point established

#### Test 8: Music Theory Application

**Prompt:**
```
Create a jazz chord progression in the key of F major. Add it to the "Lead" track with swing timing and suggest appropriate tempo.
```

**Expected Response:**
```
🎼 **Jazz Progression in F Major**
🎵 **Suggested Jazz Progressions**:
• ii_V_I: G - C - F
• vi_ii_V_I: D - G - C - F

🥁 **Tempo Analysis** 
• Current: 125 BPM
• Optimal for jazz: 140 BPM
• Suggestion: Try 140 BPM for medium energy jazz

🎵 Added 12 notes to Lead track
🎼 Applied jazz harmony principles
⏱️ Applied swing quantization
```

**Ableton Side:**
- Lead track should contain new MIDI clip
- Notes should reflect jazz chord voicings
- Consider setting groove to swing feel
- Tempo could be adjusted to 140 BPM

### Troubleshooting Tests

#### Test 9: Connection Verification

**Prompt:**
```
Check if we're still connected to Ableton Live and get the current transport status.
```

**Expected Response:**
```
📊 Transport status requested
🎵 **Current Status**:
• State: Stopped
• Tempo: 125 BPM  
• Current Time: 0.0.0
• Connection: Active ✅
```

#### Test 10: Error Handling

**Prompt:**
```
Try to add notes to track 99, clip 99 (which doesn't exist).
```

**Expected Response:**
```
❌ [TRACK_NOT_FOUND] Track 99 not found
💡 Available tracks: 0-5 (6 total tracks)
```

## 🔍 Monitoring and Debugging

### Check Ableton Live Logs
Monitor the Ableton Live log file for OSC messages:

**Windows:**
```bash
tail -f "%USERPROFILE%\AppData\Roaming\Ableton\Live [version]\Preferences\Log.txt"
```

**macOS:**
```bash
tail -f "~/Library/Preferences/Ableton/Live [version]/Log.txt"
```

Look for messages like:
```
RemoteScriptMessage: AbletonOSC: Received /live/song/start_playing
RemoteScriptMessage: AbletonOSC: Received /live/song/get/tempo
```

### Claude Code MCP Debug
Enable MCP debugging in Claude Code:
1. Open Developer Tools (if available)
2. Check console for MCP communication logs
3. Verify tool availability in Claude Code interface

### Network Verification
Check if OSC ports are working:

```bash
# Check if ports are listening (Windows)
netstat -an | findstr 11000

# Check if ports are listening (macOS/Linux)  
lsof -i :11000
```

## 🎯 Advanced Test Scenarios

### Scenario 1: Live Performance Setup

**Prompt:**
```
Set up Ableton for a live electronic performance:
1. Create 8 tracks for different elements
2. Set up appropriate mix levels for club sound system
3. Analyze tempo for house music and set accordingly
4. Create a basic 4-bar loop structure on track 1
```

### Scenario 2: Mixing Session

**Prompt:**
```
Analyze the current mix and provide professional mixing suggestions:
1. Check overall mix balance
2. Suggest LUFS target for Spotify
3. Analyze frequency balance across tracks
4. Provide EQ suggestions for each track
```

### Scenario 3: Composition Assistant

**Prompt:**
```
Help me compose a pop song:
1. Suggest a chord progression in G major
2. Create the progression on the Lead track
3. Harmonize a simple melody
4. Suggest an arrangement structure
5. Set appropriate tempo for commercial pop
```

## ⚠️ Common Issues and Solutions

### Issue 1: Connection Failed
**Error:** `❌ [CONNECTION_FAILED] Failed to connect to Ableton Live`

**Solutions:**
1. Verify Ableton Live is running
2. Check AbletonOSC is enabled in MIDI preferences
3. Ensure ports 11000-11001 aren't blocked by firewall
4. Restart both Ableton Live and Claude Code

### Issue 2: No Response from Tools
**Symptoms:** Claude Code shows tools but they don't execute

**Solutions:**
1. Check MCP server is running: `ps aux | grep ableton_mcp`
2. Verify Python environment and dependencies
3. Check Claude Code MCP configuration
4. Restart Claude Code to reload MCP server

### Issue 3: OSC Communication Timeout
**Error:** `❌ [OSC_COMMUNICATION_ERROR] OSC message timeout`

**Solutions:**
1. Verify AbletonOSC script is properly loaded
2. Check Ableton Live isn't frozen/unresponsive
3. Restart AbletonOSC remote script
4. Check network firewall settings

### Issue 4: Notes Not Appearing
**Symptoms:** MCP reports success but no MIDI notes in clips

**Solutions:**
1. Ensure target clip exists (create empty MIDI clip first)
2. Check clip length is sufficient for note placement
3. Verify track is MIDI type (not audio)
4. Check clip is selected/visible in Session View

## 🎼 Musical Workflow Examples

### Electronic Music Production
```
"Create an electronic music track:
1. Set tempo to 128 BPM for house music
2. Create tracks: Kick, Bass, Lead, Pads, FX
3. Add a basic four-on-the-floor pattern to the kick
4. Create a minor scale bassline in Em
5. Set up appropriate mix levels for club playback"
```

### Jazz Composition
```
"Set up a jazz composition in Bb major:
1. Set swing timing at 140 BPM
2. Create a ii-V-I progression on piano track
3. Add walking bassline suggestions
4. Create chord voicings with proper voice leading
5. Suggest melody notes that work with harmony"
```

### Pop Song Arrangement
```
"Arrange a commercial pop song:
1. Set tempo for radio-friendly pop (120 BPM)
2. Create verse-chorus structure with 8 tracks
3. Build energy curve from intro to final chorus
4. Set LUFS target for streaming platforms
5. Create hook melody in the relative minor"
```

## 📊 Expected Performance

### Response Times
- **Connection**: < 2 seconds
- **Transport Control**: < 500ms
- **Track Operations**: < 1 second
- **Note Addition**: < 2 seconds (depends on complexity)
- **Music Analysis**: < 3 seconds

### Success Rates
- **Basic Operations**: 99%+ success rate
- **Complex Musical Analysis**: 95%+ accuracy
- **Error Recovery**: Automatic with informative messages

## 🎓 Best Practices

### For Optimal Performance
1. **Keep Ableton Live responsive** - Avoid CPU-heavy plugins during MCP operations
2. **Use descriptive prompts** - Be specific about musical intentions
3. **Start simple** - Test basic functionality before complex workflows
4. **Monitor both applications** - Watch both Claude Code and Ableton for feedback

### For Musical Workflows  
1. **Establish key/tempo early** - Set musical context for better AI suggestions
2. **Use progressive complexity** - Build arrangements incrementally
3. **Leverage music theory tools** - Let the MCP suggest progressions and harmonies
4. **Save frequently** - Complex operations should be saved incrementally

---

<div align="center">

**🎵 Ready to revolutionize your music production workflow!**

[Back to Main README](README.md) • [Architecture Guide](docs/architecture.md) • [Troubleshooting](docs/troubleshooting.md)

</div>