# HockeyVision — AI Hockey Video Analysis
## Technical Spec & Development Plan

Status: Experimental / MVP
Primary goal: Analyze hockey game footage and generate player-specific coaching reports
Initial target: CEGEP-level hockey footage from elevated rink-side camera angles

---

# 1. Product Goal

HockeyVision analyzes full hockey game video and allows a coach to request:

"Analyze player #89's shifts and give me a report."

The system should:

1. detect players in the video
2. track players across frames
3. identify the requested player's jersey number
4. determine when that player is on/off the ice
5. extract the player's shifts
6. calculate basic movement and game statistics
7. identify important hockey events
8. generate a coaching report
9. provide clips supporting the report

Long-term goal:

Coach uploads game video -> HockeyVision processes it -> coach can query game using natural language.

Example queries:

- Analyze #89's game
- Show all shifts for #89
- Show all of #89's offensive-zone entries
- Show his turnovers
- Compare period 1 vs period 3
- Show every shot attempt by #89
- Which shifts were longer than 50 seconds?
- Show clips where #89 failed to backcheck

---

# 2. Core Principle

HockeyVision should NOT begin as:

video -> LLM -> report

Instead:

video
  ↓
computer vision
  ↓
structured hockey data
  ↓
statistics / events
  ↓
LLM
  ↓
coaching report

The computer vision pipeline is the actual ML system.

The LLM is only responsible for interpreting structured results and writing a readable coaching report.

---

# 3. Initial Footage Assumptions

Initial training/testing footage comes mostly from existing CEGEP hockey recordings.

Typical characteristics:

- elevated spectator / press-box angle
- camera sees roughly 1/2 to 2/3 of rink
- camera pans during play
- 1080p or similar video
- standard broadcast-style landscape format
- players relatively small in frame
- jersey numbers sometimes visible
- players frequently overlap
- puck is extremely small
- boards/glass partially obstruct lower portions of frame
- camera occasionally loses players during transitions

This footage is good enough for player detection/tracking.

Jersey identification and puck tracking will be substantially harder.

---

# 4. MVP Definition

The MVP is NOT full automated hockey analytics.

MVP success:

Upload a game and reliably obtain:

- all detected players
- one selected player's tracking
- estimated time on ice
- detected shifts
- shift clips
- player movement heatmap
- average / longest shift
- approximate skating distance
- approximate position on ice
- AI-generated summary from these results

Initial player identification may be semi-automatic.

Example:

Coach chooses:

Player: #89

System displays several candidate player crops.

Coach confirms:

"This is #89."

The tracker then follows the confirmed player.

This is acceptable for V1.

---

# 5. Development Phases

## Phase 0 — Video Pipeline

Goal:

Read hockey video reliably and process frames.

Features:

- video upload
- metadata extraction
- frame extraction
- configurable FPS processing
- timestamp tracking
- video clipping
- thumbnail generation

Tools:

Python
OpenCV
FFmpeg

Example:

input:
game.mp4

output:

metadata.json
frames/
clips/

Do NOT run ML on every 60 FPS frame initially.

Target:

5-15 FPS during development.

---

# 6. Phase 1 — Player Detection

Goal:

Detect every skater, goalie and referee.

Possible model:

YOLO

Initial classes:

player
goalie
referee

Puck can be excluded initially.

Model output per frame:

[
  {
    "class": "player",
    "confidence": 0.94,
    "bbox": [x1, y1, x2, y2]
  }
]

Training dataset should come primarily from the user's own footage.

---

# 7. Dataset Creation

Start by extracting frames from multiple games.

Do NOT label consecutive frames only.

Sample different:

- arenas
- camera zoom levels
- periods
- lighting
- teams
- jersey colors
- offensive/defensive zones
- neutral zone
- crowded plays
- breakaways
- benches

Initial target:

1,000-2,000 annotated frames.

Potentially:

10-20 players per frame

This gives approximately:

10,000-30,000 player bounding boxes.

Split:

70% train
20% validation
10% test

Important:

Frames from the SAME GAME should not appear across train and test sets.

Otherwise model performance may look artificially good.

---

# 8. Annotation

Recommended annotation tools:

CVAT
Roboflow
Label Studio

Initial labels:

player
goalie
referee

Possible future labels:

puck
net
bench
official
team_A_player
team_B_player

Do not start with too many classes.

---

# 9. Phase 2 — Player Tracking

Goal:

Maintain player identity between frames.

Example:

Frame 100:
player_track_id = 14

Frame 101:
player_track_id = 14

Frame 102:
player_track_id = 14

Possible trackers:

ByteTrack
BoT-SORT

Pipeline:

YOLO
  ↓
bounding boxes
  ↓
tracker
  ↓
persistent track IDs

Output:

{
  "track_id": 14,
  "timestamp": 642.31,
  "bbox": [...]
}

---

# 10. Tracking Challenges

Expected issues:

- player-player occlusion
- board/glass obstruction
- camera pan
- players leaving frame
- players entering bench
- identical uniforms
- line changes
- goalie equipment
- refs intersecting player paths

Tracking IDs WILL switch sometimes.

MVP should tolerate this.

Perfect tracking is not required initially.

---

# 11. Phase 3 — Team Classification

Before jersey numbers, determine which team each player belongs to.

Possible approach:

Extract player torso crop.

Calculate dominant jersey colors.

Classify:

home
away
official

Example:

track 14:
team = white

track 8:
team = dark

This significantly reduces the search space for jersey-number recognition.

---

# 12. Phase 4 — Player Identification

Goal:

Associate track:

track_id 14

with:

player #89

This is difficult.

Use multiple signals.

## Signal 1 — Jersey Number OCR

Crop player jersey.

Attempt digit recognition.

Possible models:

OCR
custom digit classifier
YOLO digit detector

Predictions over multiple frames:

frame 120: 89
frame 121: ??
frame 122: 89
frame 123: 89
frame 124: 8?

Aggregate:

#89 confidence = 0.91

Never rely on a single frame.

---

# 13. Semi-Automatic Identification

Initial version should allow human confirmation.

Workflow:

System finds candidate players.

Displays representative crops:

Candidate A
Candidate B
Candidate C

Coach selects:

"#89"

System associates:

track / identity cluster -> roster player #89

This dramatically simplifies V1.

Full automatic jersey recognition comes later.

---

# 14. Player Re-Identification

Eventually tracking should survive:

- leaving frame
- line change
- returning later
- jersey OCR failures

Possible ReID features:

jersey number
team
helmet color
equipment colors
body appearance embedding
position history

Player identity should exist ABOVE tracker ID.

Example:

PlayerIdentity:
player_id = 89

Associated track IDs:

14
38
61
92

because the tracker may assign new IDs after every shift.

---

# 15. Phase 5 — Shift Detection

Once #89 is identifiable:

Determine when he enters and exits the ice.

Possible heuristic:

shift begins:
player detected inside playing surface for > N frames

shift ends:
player absent from playing surface for > N seconds

Example:

Shift 1:
02:12 - 02:53
duration: 41 sec

Shift 2:
05:31 - 06:19
duration: 48 sec

Shift 3:
08:44 - 09:20
duration: 36 sec

Store automatically generated clips for each shift.

---

# 16. Bench / Ice Classification

Need to distinguish:

player on ice

vs

player sitting/standing on bench

Use rink geometry.

Create rink mask:

PLAY AREA
BENCH
STANDS
BOARDS

A player bounding box centroid inside the rink polygon counts as active.

This can initially be manually calibrated per arena/video.

---

# 17. Rink Calibration

Because the camera moves and perspective is distorted, raw pixel coordinates are not meaningful.

Eventually map video coordinates onto a standard hockey rink.

Input:

pixel coordinate

Output:

rink coordinate

Example:

video:
(x=935, y=430)

mapped:

rink:
(x=72 ft, y=31 ft)

Possible methods:

homography
rink-line detection
faceoff-circle detection
blue/red line detection

V1 may manually define landmarks.

---

# 18. Phase 6 — Movement Analytics

Once rink coordinates are available, calculate:

- location history
- heatmap
- estimated distance travelled
- average speed
- max estimated speed
- offensive-zone time
- defensive-zone time
- neutral-zone time
- shift length
- location at shift start/end

Example output:

Player #89

TOI: 14:22
Shifts: 19
Average shift: 45.4 sec
Longest shift: 71 sec

Zone time:

Offensive: 5:31
Neutral: 3:02
Defensive: 5:49

---

# 19. Phase 7 — Puck Detection

This should NOT be an early requirement.

The puck is one of the hardest objects in the project because it is:

- tiny
- black
- fast
- motion-blurred
- frequently blocked
- often hidden against sticks/skates/boards

Train a dedicated puck model later.

Use higher resolution crops / frames.

Possible techniques:

YOLO
temporal tracking
motion cues
multi-frame prediction

Puck tracking failure must not break the rest of HockeyVision.

---

# 20. Phase 8 — Hockey Event Detection

Initial detectable events:

shot attempt
zone entry
zone exit
pass
puck recovery
turnover

Later:

controlled entry
dump-in
forecheck
backcheck
hit
scoring chance
screen
board battle

Do NOT try to detect all hockey concepts immediately.

---

# 21. Event Representation

Example:

{
  "event_id": "...",
  "game_id": "...",
  "player_id": 89,
  "timestamp": 642.4,
  "type": "zone_entry",
  "subtype": "controlled",
  "confidence": 0.87
}

Another:

{
  "player_id": 89,
  "timestamp": 701.2,
  "type": "shot_attempt",
  "confidence": 0.93
}

---

# 22. Event Detection Strategy

Some events can be rule-based before using dedicated neural networks.

Example:

ZONE ENTRY

if:

player crosses offensive blue line

AND

puck/player relationship suggests possession

THEN

zone_entry

Other events may require temporal ML.

Input:

2-5 seconds of video

Output:

event class

Potential models:

3D CNN
Video Transformer
LSTM over extracted features

These should come much later.

---

# 23. HockeyVision Report

After computer vision analysis, produce structured statistics.

Example:

{
  "player": 89,
  "toi": "14:32",
  "shifts": 19,
  "avg_shift": 45.9,
  "longest_shift": 68,
  "zone_entries": 5,
  "shots": 4,
  "turnovers": 2
}

Then send structured data to an LLM.

Prompt:

"You are assisting a hockey coach.

Analyze the following player performance data.

Do not invent events not present in the data.

Identify patterns, strengths, concerns and specific coaching points."

---

# 24. Report Format

## Player #89 Game Report

Ice Time:
14:32

Shifts:
19

Average Shift:
46 sec

Longest Shift:
68 sec

### Offensive Play

- 5 zone entries
- 3 controlled entries
- 4 shot attempts
- 7 completed passes

### Defensive Play

- 4 recoveries
- 3 successful exits
- 2 failed defensive transitions

### Shift Management

Several shifts exceeded 50 seconds.

Performance metrics declined during longer shifts.

### Coaching Observations

...

### Recommended Focus

...

### Supporting Clips

Shift 4
Shift 7
Shift 13

Each observation should link to timestamp/video evidence where possible.

---

# 25. Natural Language Query Layer

Future UI:

Ask HockeyVision:

"Focus on #89's shifts. Give me a report."

Query parser determines:

player = 89
scope = shifts
operation = report

Other queries:

"Show turnovers by #89."

player = 89
event = turnover

"Show shifts longer than 50 seconds."

filter:
shift_duration > 50

The LLM should query structured HockeyVision data rather than directly inspect raw video.

---

# 26. System Architecture

Mobile App
    |
    | REST API
    v
HockeyVision Backend
    |
    +-- Video Service
    |
    +-- Detection Service
    |
    +-- Tracking Service
    |
    +-- Identity Service
    |
    +-- Analytics Service
    |
    +-- Report Service
    |
    +-- Clip Service
    |
    v
Database / Object Storage

ML components should remain independent from the mobile application.

---

# 27. Suggested ML Backend Stack

Python 3.11+

FastAPI

PyTorch

Ultralytics YOLO

OpenCV

FFmpeg

NumPy

Pandas

ByteTrack / BoT-SORT

PostgreSQL / Supabase

Optional later:

Redis
Celery
Docker
ONNX
ROCm
CUDA

---

# 28. GPU Environment

Current development GPU:

AMD Radeon RX 9060 XT
16 GB VRAM

Primary ML backend:

PyTorch + ROCm

Initial target models should comfortably fit inside 16 GB VRAM.

Development strategy:

- start with small/medium YOLO models
- use mixed precision
- reduce image size/batch size when required
- cache/preprocess video
- avoid unnecessarily large models

CUDA should NOT be considered a requirement.

If a library requires CUDA-only functionality, evaluate:

1. alternative library
2. CPU implementation
3. ROCm-compatible method
4. cloud NVIDIA GPU

before changing hardware.

---

# 29. Local Development Workflow

MacBook:

coding
annotation management
API development
mobile development
database work

Desktop / RX 9060 XT:

dataset processing
training
inference benchmarking
batch game processing

---

# 30. Repository Structure

hockeyvision/

  README.md

  api/
    main.py
    routes/
    schemas/

  vision/
    detection/
    tracking/
    identification/
    rink/
    puck/
    events/

  training/
    player_detection/
    jersey_numbers/
    puck_detection/
    events/

  datasets/
    scripts/
    configs/

  analytics/
    shifts.py
    movement.py
    zones.py

  reports/
    report_generator.py
    prompts/

  video/
    extract_frames.py
    clips.py
    ffmpeg.py

  tests/

  configs/

  notebooks/

---

# 31. Database Model

HockeyVideo

id
game_id
storage_path
duration
fps
resolution
processing_status
created_at

VisionPlayer

id
video_id
roster_player_id nullable
jersey_number nullable
team
identity_confidence

PlayerTrack

id
vision_player_id
track_id
start_time
end_time

PlayerPosition

track_id
timestamp
pixel_x
pixel_y
rink_x nullable
rink_y nullable
confidence

Shift

id
player_id
video_id
start_time
end_time
duration
clip_path

VisionEvent

id
video_id
player_id nullable
event_type
timestamp
confidence
metadata

VisionReport

id
video_id
player_id
report_json
report_text
created_at

---

# 32. Integration with Existing Coaching App

The existing app should not process video locally.

Flow:

React Native app
   ↓
upload game video
   ↓
HockeyVision backend
   ↓
analysis job
   ↓
database
   ↓
app fetches results

Possible game screen addition:

Game
├── Lineup
├── Notes
├── HockeyVision
│
├── Upload Video
├── Processing Status
├── Player Reports
└── Ask HockeyVision

HockeyVision should reference existing:

game_id
team_id
player_id

rather than duplicate roster/game data.

---

# 33. Processing Jobs

Video processing will take time.

Do not use a normal synchronous HTTP request.

Workflow:

POST /analysis

Response:

{
  "job_id": "abc123",
  "status": "queued"
}

Processing:

queued
↓
extracting
↓
detecting
↓
tracking
↓
identifying
↓
analyzing
↓
reporting
↓
complete

App polls or subscribes for status updates.

---

# 34. Initial APIs

POST /videos

Upload/register video.

POST /videos/{video_id}/analyze

Start analysis.

GET /analysis/{job_id}

Processing status.

GET /videos/{video_id}/players

Detected players.

POST /videos/{video_id}/players/{vision_player_id}/link

Associate detected player with roster player.

GET /videos/{video_id}/players/{player_id}/shifts

Return player shifts.

GET /videos/{video_id}/players/{player_id}/report

Return report.

POST /videos/{video_id}/query

Natural language HockeyVision query.

---

# 35. Evaluation Metrics

## Player Detection

mAP50
precision
recall

Initial target:

>90% player recall on representative footage.

Missing a player is worse than occasionally detecting a false player.

## Tracking

ID switches
track fragmentation
HOTA / IDF1 eventually

Practical target:

player remains same track during majority of a single shift.

## Jersey Identification

accuracy over confirmed visible-number segments.

Target:

>90% when number is clearly visible.

Do not expect 90% across every frame.

## Shift Detection

Compare manually labeled shifts vs predicted.

Measure:

start-time error
end-time error
duration error

Initial target:

±3 seconds.

---

# 36. Development Roadmap

## Week 1

Set up repository.

Install:

Python
PyTorch
ROCm
OpenCV
FFmpeg
YOLO

Process one full hockey video.

Extract frames.

Benchmark processing speed.

---

## Week 2

Build initial dataset.

Extract approximately 1,000 representative frames.

Begin player annotations.

Create:

player
goalie
referee

classes.

---

## Week 3

Train first player detector.

Evaluate on completely unseen game footage.

Generate annotated test video with bounding boxes.

Milestone:

HockeyVision can reliably locate players.

---

## Week 4

Integrate ByteTrack or BoT-SORT.

Generate persistent player tracks.

Export:

track ID
timestamp
bounding box

Milestone:

players can be followed during continuous play.

---

## Week 5

Add team classification.

Home / away / referee classification.

Generate track summaries.

---

## Week 6

Build manual player-identification interface.

User selects:

#89

from detected player candidates.

Associate tracks with selected player.

Milestone:

system can follow one chosen player.

---

## Week 7

Implement shift detection.

Generate:

shift start
shift end
duration
video clip

Milestone:

"Show me #89's shifts."

---

## Week 8

Create initial rink mapping.

Manually identify rink landmarks.

Generate:

player trajectory
heatmap
zone time

---

## Week 9

Generate player statistics.

TOI
shift count
average shift
longest shift
zone distribution
movement metrics

---

## Week 10

Build report generator.

Structured statistics -> LLM report.

Milestone:

"Analyze #89's shifts and give me a report."

---

## Week 11

Integrate backend API.

FastAPI endpoints.

Connect video/job/player/report data.

---

## Week 12

Integrate into coaching app.

Add:

HockeyVision game tab
processing screen
player selector
report screen
shift clips

---

# 37. V1 Success Criteria

V1 is successful if:

A coach uploads a game.

The system processes the game.

The coach identifies #89.

HockeyVision automatically finds most of #89's shifts.

The app displays:

- total ice time
- shifts
- average shift length
- movement heatmap
- zone time
- all shift clips

The system generates a basic coaching report based on those metrics.

This alone is a strong ML project.

Puck/event detection is NOT required for V1.

---

# 38. V2

Add:

automatic jersey-number recognition
automatic player identity
puck tracking
shot detection
zone entries/exits
pass detection
turnovers
puck recoveries

---

# 39. V3

Add:

possession estimation
scoring chances
defensive coverage analysis
forechecking analysis
backchecking analysis
line chemistry
team structure
expected goals
automatic tactical analysis

---

# 40. Biggest Technical Risks

1. Jersey number visibility

The number is often hidden.

Solution:

multi-frame voting + manual confirmation.

2. Tracking through occlusions

Players frequently overlap.

Solution:

ReID + identity merging.

3. Puck tracking

Extremely difficult.

Do not make this an MVP dependency.

4. Camera movement

Pixel coordinates move when camera pans.

Need rink calibration.

5. Training data

High-quality labels matter more than simply collecting massive amounts of footage.

6. Processing cost

A 2-hour game contains hundreds of thousands of frames.

Need frame sampling and efficient inference.

---

# 41. First Concrete Milestone

Do NOT begin by training puck detection or jersey OCR.

The first objective should be:

INPUT:
one of the user's existing CEGEP games

OUTPUT:
same video with a bounding box and persistent tracking ID drawn over every player.

Example:

[#14]
[#21]
[#38]
[#7]

If this works reliably, the foundation of HockeyVision exists.

Then select one player and solve:

"keep tracking THIS player."

Everything else builds from there.