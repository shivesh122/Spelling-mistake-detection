from flask import Flask, request, jsonify, render_template_string
from typing import List, Dict, Optional
import jellyfish
import math
import time
import threading
import webbrowser

app = Flask(__name__)


EN_WORDS = [
    "a","an","and","away","big","blue","can","come","down","find","for","fun","get","go","had","has","have","he","help","here","i","in","is","it","jump","little","look","make","me","my","not","now","on","one","play","red","run","said","see","she","the","they","this","three","to","two","up","want","we","where","yellow","you","all","am","are","at","be","by","do","does","done","from","if","into","its","let","may","more","much","no","of","off","or","out","put","so","some","then","there","these","those","time","toy","use","very","was","what","when","who","why","yes","yet","your","after","again","around","ask","away","back","because","before","best","both","buy","call","came","change","close","cut","draw","every","fast","find","fly","give","goes","good","had","hear","keep","kind","know","like","live","long","look","make","man","men","most","must","name","near","never","new","old","once","only","open","own","play","put","read","ride","run","said","see","show","sing","sit","sleep","small","stand","stop","take","tell","think","try","under","walk","want","watch","well","will","work","write","yourself","his","her","hers","him","their","theirs","ours","myself","yourself","ourselves","themselves","this","that","these","those","itself","each","every","any","some","few","many","lot","number","first","second","third","next","last","other","right","left","up","down","here","there","over","under","again","soon","later","now","then","always","never","sometimes","often","today","tomorrow","yesterday","day","night","morning","evening","time","school","home","family","friend","teacher","student","bag","book","pen","pencil","eraser","sharpener","desk","bench","board","class","learn","read",
]

HI_WORDS = [
    "सेब","बिल्ली","कुत्ता","घर","माता","पिता","खेल","किताब","स्कूल","फूल","गाय","सूरज","चाँद","नदी","आनंद","खुश","बच्चा","मित्र","दोस्त","सफर","पेड़","पत्ता","पानी","धरती","आसमान","पक्षी","फल","सब्जी","बाजार","शहर","गांव","सड़क","रेल","बस","गाड़ी","खिलौना","मैदान","कहानी","खेलना","पढ़ना","लिखना","सुनना","बोलना","मदद","साझा","मुस्कान","अच्छा","साफ","सुंदर","ईमानदार","दयालु","सच्चा","सूरजमुखी","बारिश","ठंड","गर्मी","वसंत","पतझड़","आशा","विश्व","काम","समय","दोस्ताना","विद्यालय","शिक्षक","विद्यार्थी","पेंसिल","कलम","रबर","किताब","बैग","डेस्क","बेंच","ब्लैकबोर्ड","चॉक","संख्या","रंग","आकार","जानवर","पंछी","फल","सब्ज़ी","शहर","गांव","नदी","बगीचा","पार्क","कुत्ता","बिल्ली","शेर","हाथी","बंदर","सिंह","मोर","तोता","खरगोश","खाना","दूध","पानी","दोस्ती","परिवार","भाई","बहन","खुशी","आनंद","सपना","सुबह","शाम","दिन","रात","आज","कल","कलमदान","कक्षा","कापी","खिड़की","दरवाज़ा","कमरा","घड़ी","समझ","सीखना","सुनना","पढ़ाई","खेलकूद","सफाई","स्वास्थ्य","प्रकृति","जीवन","प्रेम","ईश्वर","सत्य","धैर्य","सम्मान","ईमान","भोजन","फल","दूध","पानी","वातावरण","पशु","पक्षी","मनुष्य","मित्रता","संगीत","चित्र","नृत्य","गीत","कविता",
]

VOCAB: Dict[str, Dict] = {}

def age_level_for(word: str) -> str:
    l = len(word)
    if l <= 3:
        return "3-4"
    if l <= 6:
        return "5-6"
    return "7-8"

for w in EN_WORDS:
    wl = w.lower()
    VOCAB[wl] = {
        "lang": "english",
        "phonetic": jellyfish.metaphone(wl) or "",
        "age_level": age_level_for(wl),
        "difficulty": 1 if len(wl) <= 4 else (2 if len(wl) <= 7 else 4),
        "category": "general",
        "frequency": "high",
        "example_sentence": f"I see a {wl}",
        "audio_pronunciation": None,
        "image_reference": None,
        "common_mistakes": [],
        "teaching_tips": None
    }

for w in HI_WORDS:
    VOCAB[w] = {
        "lang": "hindi",
        "phonetic": "",
        "age_level": age_level_for(w),
        "difficulty": 1 if len(w) <= 3 else (2 if len(w) <= 6 else 4),
        "category": "general",
        "frequency": "high",
        "example_sentence": f"यह एक {w} है",
        "audio_pronunciation": None,
        "image_reference": None,
        "common_mistakes": [],
        "teaching_tips": None
    }

for k in ["apple", "phone", "elephant", "beautiful"]:
    if k in VOCAB:
        VOCAB[k]["common_mistakes"] = [{"incorrect": "aple" if k=="apple" else "fone" if k=="phone" else "elefant", "error_type":"common"}]


def damerau_levenshtein(a: str, b: str) -> int:
    a = a or ""
    b = b or ""
    len_a = len(a)
    len_b = len(b)
    INF = len_a + len_b
    dp = [[0] * (len_b + 2) for _ in range(len_a + 2)]
    dp[0][0] = INF
    for i in range(len_a + 1):
        dp[i + 1][1] = i
        dp[i + 1][0] = INF
    for j in range(len_b + 1):
        dp[1][j + 1] = j
        dp[0][j + 1] = INF
    da = {}
    for i in range(1, len_a + 1):
        db = 0
        for j in range(1, len_b + 1):
            i1 = da.get(b[j - 1], 0)
            j1 = db
            cost = 0 if a[i - 1] == b[j - 1] else 1
            if cost == 0:
                db = j
            dp[i + 1][j + 1] = min(
                dp[i][j] + cost,
                dp[i + 1][j] + 1,
                dp[i][j + 1] + 1,
                dp[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1) if (i1 and j1) else INF
            )
        da[a[i - 1]] = i
    return dp[len_a + 1][len_b + 1]

def phonetic_code(word: str) -> str:
    try:
        return jellyfish.metaphone(word) or ""
    except Exception:
        return ""

class Vocabulary:
    def __init__(self, data: Dict[str, Dict]):
        self.db = {k: v for k, v in data.items()}
        self.phonetic_index = {}
        for w, meta in self.db.items():
            if meta.get("lang") == "english":
                p = phonetic_code(w)
                if p:
                    self.phonetic_index.setdefault(p, []).append(w)

    def exists(self, word: str, language: Optional[str] = None, age_level: Optional[str] = None) -> bool:
        if not word:
            return False
        if word in self.db:
            if language and self.db[word].get("lang") != language:
                return False
            if age_level and self.db[word].get("age_level") != age_level:
                return False
            return True
        lw = word.lower()
        if lw in self.db:
            if language and self.db[lw].get("lang") != language:
                return False
            if age_level and self.db[lw].get("age_level") != age_level:
                return False
            return True
        return False

    def get(self, word: str) -> Optional[Dict]:
        if not word:
            return None
        if word in self.db:
            return self.db[word]
        return self.db.get(word.lower())

    def all_words(self, language: Optional[str] = None) -> List[str]:
        if not language:
            return list(self.db.keys())
        return [w for w, m in self.db.items() if m.get("lang") == language]

    def find_by_phonetic(self, word: str) -> List[str]:
        return self.phonetic_index.get(phonetic_code(word), [])

    def documented_mistake(self, candidate: str, misspelled: str) -> bool:
        meta = self.get(candidate)
        if not meta:
            return False
        for cm in meta.get("common_mistakes", []):
            if cm.get("incorrect") == misspelled:
                return True
        return False

vocab = Vocabulary(VOCAB)

class SpellingSuggester:
    def __init__(self, vocab: Vocabulary):
        self.vocab = vocab

    def get_suggestions(self, word: str, language: Optional[str] = None, age_level: Optional[str] = None, max_suggestions: int = 4):
        miss = (word or "")
        candidates = []
        search_space = self.vocab.all_words(language) if language else self.vocab.all_words()
        for w in search_space:
            if w == miss:
                continue
            try:
                dist = damerau_levenshtein(miss.lower(), w.lower())
            except Exception:
                dist = 99
            if dist <= 2:
                candidates.append((w, dist))
        if language in (None, "english"):
            for w in self.vocab.find_by_phonetic(miss):
                candidates.append((w, 2))
        documented = []
        for w in search_space:
            if self.vocab.documented_mistake(w, miss):
                documented.append((w, 0))
        combined = {}
        for w, d in documented + candidates:
            if w in combined:
                combined[w] = min(combined[w], d)
            else:
                combined[w] = d
        scored = []
        for w, dist in combined.items():
            meta = self.vocab.get(w) or {}
            score = 1 / (1 + dist)
            if meta.get("frequency") == "high":
                score += 0.25
            if self.vocab.documented_mistake(w, miss):
                score += 0.35
            if age_level and meta.get("age_level") == age_level:
                score += 0.15
            scored.append({"word": w, "score": round(score, 2), "phonetic": meta.get("phonetic")})
        return sorted(scored, key=lambda x: x["score"], reverse=True)[:max_suggestions]

def align_and_classify(written: str, correct: str) -> List[Dict]:
    written = written or ""
    correct = correct or ""
    i = j = 0
    mistakes = []
    while i < len(written) and j < len(correct):
        if written[i] == correct[j]:
            i += 1; j += 1; continue
        if i+1 < len(written) and j+1 < len(correct) and written[i] == correct[j+1] and written[i+1] == correct[j]:
            mistakes.append({"position_written": i, "position_correct": j, "error_type": "transposition", "written": written[i:i+2], "correct": correct[j:j+2]})
            i += 2; j += 2; continue
        if len(written) - i > len(correct) - j:
            mistakes.append({"position_written": i, "position_correct": j, "error_type": "extra_letter", "written": written[i], "correct": None})
            i += 1; continue
        if len(correct) - j > len(written) - i:
            mistakes.append({"position_written": i, "position_correct": j, "error_type": "missing_letter", "written": None, "correct": correct[j]})
            j += 1; continue
        mistakes.append({"position_written": i, "position_correct": j, "error_type": "wrong_letter", "written": written[i], "correct": correct[j]})
        i += 1; j += 1
    while i < len(written):
        mistakes.append({"position_written": i, "position_correct": None, "error_type": "extra_letter", "written": written[i], "correct": None})
        i += 1
    while j < len(correct):
        mistakes.append({"position_written": None, "position_correct": j, "error_type": "missing_letter", "written": None, "correct": correct[j]})
        j += 1
    return mistakes

class MistakeAnalyzer:
    def __init__(self, vocab: Vocabulary):
        self.vocab = vocab
        self.suggester = SpellingSuggester(vocab)

    def find_intended_word(self, written_word: str, language: Optional[str] = None, age_level: Optional[str] = None) -> str:
        if self.vocab.exists(written_word, language=language, age_level=age_level):
            return written_word
        suggestions = self.suggester.get_suggestions(written_word, language=language, age_level=age_level, max_suggestions=1)
        if suggestions:
            return suggestions[0]["word"]
        best = None
        best_d = math.inf
        space = self.vocab.all_words(language) if language else self.vocab.all_words()
        for w in space:
            try:
                d = damerau_levenshtein(written_word.lower(), w.lower())
            except Exception:
                d = 99
            if d < best_d:
                best_d = d
                best = w
        return best or written_word

    def analyze_mistake(self, written_word: str, child_profile: dict):
        language = child_profile.get("language") if child_profile and child_profile.get("language") else None
        age = child_profile.get("ageGroup") if child_profile else None
        intended = self.find_intended_word(written_word, language=language, age_level=age)
        positions = align_and_classify(written_word, intended)
        types = {p["error_type"] for p in positions}
        if "missing_letter" in types:
            main = "missing_letter"
        elif "extra_letter" in types:
            main = "extra_letter"
        elif "transposition" in types:
            main = "transposition"
        else:
            main = "wrong_letter"
        return {"written_word": written_word, "intended_word": intended, "type": main, "positions": positions, "common_mistake": self.vocab.documented_mistake(intended, written_word), "teaching_opportunity": "Practice phonics/letters."}

analyzer = MistakeAnalyzer(vocab)

analytics_lock = threading.Lock()
analytics = {"attempts": [], "session_points": []}

def record_attempt(word: str, intended: str, correct: bool):
    ts = int(time.time())
    with analytics_lock:
        analytics["attempts"].append({"ts": ts, "word": word, "intended": intended, "correct": correct})
        total = len(analytics["attempts"])
        correct_count = sum(1 for a in analytics["attempts"] if a["correct"])
        accuracy = round((correct_count / total) * 100, 1)
        analytics["session_points"].append({"ts": ts, "accuracy": accuracy})
        analytics["session_points"] = analytics["session_points"][-300:]

@app.route("/api/v1/spelling/validate", methods=["POST"])
def api_validate():
    payload = request.get_json() or {}
    raw_word = payload.get("word") or ""
    language = (payload.get("language") or "english").lower()
    child_profile = payload.get("childProfile") or {}
    child_profile["language"] = language
    age_group = child_profile.get("ageGroup")
    query_word = raw_word if language == "hindi" else raw_word.lower()
    if vocab.exists(query_word, language=language, age_level=age_group):
        record_attempt(query_word, query_word, True)
        return jsonify({"isCorrect": True, "writtenWord": raw_word, "suggestions": [], "mistakes": [], "feedback": {"type":"correct", "message": f"Great! You spelled '{raw_word}' correctly!"}, "analytics": {"sessionPoints": analytics["session_points"]}})
    suggester = SpellingSuggester(vocab)
    suggestions = suggester.get_suggestions(query_word, language=language, age_level=age_group, max_suggestions=4)
    mistake_analysis = analyzer.analyze_mistake(query_word, child_profile)
    intended = mistake_analysis.get("intended_word") or (suggestions[0]["word"] if suggestions else "")
    record_attempt(query_word, intended, False)
    visual_mistakes = []
    for p in mistake_analysis["positions"]:
        visual_mistakes.append({"position_written": p.get("position_written"), "position_correct": p.get("position_correct"), "type": p.get("error_type"), "written": p.get("written"), "correct": p.get("correct")})
    return jsonify({"isCorrect": False, "writtenWord": raw_word, "suggestions": suggestions, "mistakes": visual_mistakes, "feedback": {"type":"incorrect", "message": f"Good try — maybe you meant '{suggestions[0]['word'] if suggestions else intended}'"}, "analytics": {"sessionPoints": analytics["session_points"]}})

@app.route("/api/v1/spelling/analyze-progress", methods=["POST"])
def api_analyze_progress():
    payload = request.get_json() or {}
    letters = payload.get("lettersWritten", []) or []
    expected = (payload.get("expectedWord") or "").strip()
    current = "".join(letters)
    if expected:
        remaining = list(expected[len(current):]) if len(expected) > len(current) else []
        status = "complete" if current == expected else "in_progress"
        return jsonify({"status": status, "currentProgress": current, "remainingLetters": remaining, "isOnTrack": expected.startswith(current), "predictions": [{"word": expected, "confidence": 0.9}], "encouragement": "Keep going!"})
    matches = [w for w in vocab.all_words() if w.startswith(current)] if current else []
    predictions = [{"word": m, "confidence": round(1.0/(1 + len(m) - len(current)), 2)} for m in matches[:5]]
    remaining_letters = list(predictions[0]["word"][len(current):]) if predictions else []
    return jsonify({"status": "in_progress" if remaining_letters else "complete", "currentProgress": current, "remainingLetters": remaining_letters, "isOnTrack": len(predictions) > 0, "predictions": predictions, "encouragement": "Nice work!"})

@app.route("/api/v1/stats/session", methods=["GET"])
def api_stats_session():
    with analytics_lock:
        return jsonify({"sessionPoints": analytics["session_points"], "attempts": analytics["attempts"][-50:]})

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Effling Kids — Spelling Demo</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: Inter, Arial, sans-serif; margin: 18px; background:#f6fbff; color:#123; }
    header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
    h1 { margin:0; font-size:20px; }
    .main { display:flex; gap:16px; }
    .left { flex:1; }
    .right { width:460px; }
    .card { background:white; border-radius:12px; padding:14px; box-shadow: 0 6px 24px rgba(15,23,42,0.06); margin-bottom:12px; }
    input[type="text"], select { padding:12px; font-size:18px; border-radius:10px; border:1px solid #e6eef9; width:70%; }
    button { padding:12px 16px; border-radius:10px; background:#1e90ff; color:white; border:none; cursor:pointer; font-weight:700; }
    .big { font-size:22px; padding:14px; }
    .suggestion { display:inline-block; padding:8px 10px; border-radius:10px; background:#eef7ff; margin-right:8px; font-weight:700; cursor:pointer; }
    .letter { display:inline-block; padding:6px 8px; margin-right:4px; border-radius:6px; font-size:20px; border:1px dashed #dbeafe; min-width:26px; text-align:center; }
    .correct { background:#ecfdf5; color:#065f46; border:1px solid #bbf7d0; }
    .wrong { background:#fff1f2; color:#9f1239; border:1px solid #fecaca; }
    .missing { background:#fff7ed; color:#92400e; border:1px solid #fed7aa; }
    .muted { color:#6b7280; font-size:13px; }
    .center { text-align:center; }
    .ok { color:#16a34a; font-weight:700; }
    .confidence { font-size:13px; margin-left:6px; padding:4px 6px; border-radius:6px; background:#f8fafc; border:1px solid #e6eef9; display:inline-block; }
    .conf-high { background:#ecfdf5; color:#065f46; border:1px solid #bbf7d0; }
    .conf-mid { background:#fff7ed; color:#92400e; border:1px solid #fed7aa; }
    .conf-low { background:#fff1f2; color:#9f1239; border:1px solid #fecaca; }
  </style>
</head>
<body>
  <header>
    <h1>Effling Kids — Spelling Practice</h1>
    <div class="muted">English & Hindi • Mock handwriting confidences</div>
  </header>

  <div class="main">
    <div class="left">
      <div class="card">
        <div style="display:flex;gap:8px;align-items:center;">
          <input id="kidInput" class="big" placeholder="Type word here (e.g., aple or सेब)" />
          <button onclick="validateWord()" title="Validate">Check</button>
        </div>
        <div style="margin-top:10px;display:flex;gap:8px;align-items:center;">
          <select id="ageSelect">
            <option value="">All ages</option>
            <option value="3-4">Age 3-4</option>
            <option value="5-6">Age 5-6</option>
            <option value="7-8">Age 7-8</option>
          </select>
          <select id="langSelect">
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
          </select>
          <button onclick="pronounceCurrent()" style="margin-left:6px;">🔊 Pronounce</button>
        </div>

        <div id="letterRow" style="margin-top:12px;"></div>

        <!-- Handwriting recognizer mock -->
        <div id="handwritingPanel" style="margin-top:12px;"></div>

        <div id="suggestions" style="margin-top:12px;"></div>

        <div id="kidFeedback" style="margin-top:12px;"></div>
      </div>

      <div class="card">
        <h3 class="center">Practice Mode — Type & get live hints</h3>
        <div class="muted" style="text-align:center;margin-top:8px;">Type letters; click Analyze for predictions</div>
        <div style="margin-top:10px;">
          <input id="liveType" style="width:100%;padding:12px;border-radius:8px;border:1px solid #e6eef9;font-size:18px" placeholder="Type letters here; try 'apple' or 'सेब'"/>
        </div>
        <div style="margin-top:10px;">
          <button onclick="analyzeLive()">Analyze</button>
          <span class="muted" style="margin-left:10px;">(Shows predictions + remaining letters)</span>
        </div>
        <div id="liveHints" style="margin-top:10px;"></div>
      </div>
    </div>

    <div class="right">
      <div class="card">
        <h3 class="center">Live Learning Progress (line chart)</h3>
        <canvas id="liveChart" width="360" height="220"></canvas>
        <div style="margin-top:8px;" class="muted center">Session accuracy over time</div>
      </div>

      <div class="card">
        <h3 class="center">Vocabulary Trainer</h3>
        <div class="muted" style="text-align:center;margin-top:6px;">Pick age-level to show sample words</div>
        <div style="margin-top:8px;">
          <select id="vocabAge" onchange="renderVocabSample()">
            <option value="">All ages</option>
            <option value="3-4">3-4</option>
            <option value="5-6">5-6</option>
            <option value="7-8">7-8</option>
          </select>
        </div>
        <div id="vocabList" style="margin-top:10px;max-height:220px;overflow:auto;"></div>
      </div>
    </div>
  </div>

<script>
  const ctx = document.getElementById('liveChart').getContext('2d');
  const chartData = { labels: [], datasets: [{ label:'Accuracy %', data:[], fill:false, tension:0.2, borderWidth:2 }] };
  const liveChart = new Chart(ctx, { type:'line', data: chartData, options:{ plugins:{legend:{display:false}}, scales:{ y:{min:0,max:100}} } });

  function speak(text, lang='en-US'){
    try {
      const ut = new SpeechSynthesisUtterance(text);
      ut.lang = lang;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(ut);
    } catch(e){ console.log("TTS not available", e); }
  }

  function playTone(type){
    try {
      const actx = new (window.AudioContext || window.webkitAudioContext)();
      const now = actx.currentTime;
      const osc = actx.createOscillator();
      const gain = actx.createGain();
      osc.connect(gain); gain.connect(actx.destination);
      if(type === 'correct'){
        osc.frequency.setValueAtTime(880, now);
        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.linearRampToValueAtTime(0.12, now + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.45);
      } else {
        osc.frequency.setValueAtTime(220, now);
        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.linearRampToValueAtTime(0.08, now + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);
      }
      osc.type = 'sine';
      osc.start(); osc.stop(now + 0.5);
    } catch(e){ console.log("Audio API error", e); }
  }

  async function renderVocabSample(){
    const age = document.getElementById('vocabAge').value;
    const container = document.getElementById('vocabList');
    container.innerHTML = '';
    const letters = ['a','b','c','d','e'];
    for(const L of letters){
      const r = await fetch('/api/v1/spelling/analyze-progress', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ lettersWritten: [L], expectedWord: "" })
      }).then(r=>r.json());
      (r.predictions || []).forEach(p => {
        const word = p.word;
        const group = word.length <=3 ? '3-4' : (word.length <=6 ? '5-6' : '7-8');
        if(age && group !== age) return;
        const node = document.createElement('div');
        node.innerHTML = `<span style="font-weight:700;margin-right:8px">${word}</span>
          <button onclick="pronounce('${word}')">🔊</button>
          <button onclick="fillWord('${word}')">Try</button>`;
        node.style.padding='6px 0';
        container.appendChild(node);
      });
    }
    if(!container.innerHTML) container.innerHTML = '<div class="muted">No sample available</div>';
  }

  function fillWord(w){ document.getElementById('kidInput').value = w; renderLettersRow(w, [], true); }

  function pronounce(word){
    const lang = document.getElementById('langSelect').value;
    if(lang === 'hindi') speak(word, 'hi-IN'); else speak(word, 'en-US');
  }
  function pronounceCurrent(){ pronounce(document.getElementById('kidInput').value.trim()); }

  // MOCK HANDWRITING: generate random confidences per letter [0.50, 1.00]
  function generateConfidences(word){
    const confs = [];
    for(let i=0;i<word.length;i++){
      // random between 0.5 and 1.0
      const v = Math.random() * 0.5 + 0.5;
      confs.push(Math.round(v*100)/100);
    }
    return confs;
  }

  // When validating a word, generate confidences and show per-letter badges
  async function validateWord(){
    const wordRaw = document.getElementById('kidInput').value.trim();
    const ageGroup = document.getElementById('ageSelect').value || null;
    const lang = document.getElementById('langSelect').value || 'english';
    if(!wordRaw){ alert('Type a word'); return; }
    // generate mock confidences client-side (simulate handwriting recognizer)
    const confidences = generateConfidences(wordRaw);
    // call validate API (server handles spelling analysis)
    const res = await fetch('/api/v1/spelling/validate', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ word: wordRaw, language: lang, childProfile: { age:5, ageGroup } })
    });
    const j = await res.json();
    // render letters with spelling mistakes
    renderLettersRow(wordRaw, j.mistakes || [], j.isCorrect, confidences);
    // render handwriting confidence panel
    renderHandwritingPanel(wordRaw, confidences);
    renderSuggestions(j.suggestions || [], j.feedback || {});
    if(j.analytics && j.analytics.sessionPoints) updateChartWith(j.analytics.sessionPoints);
    // voice + tone
    if(j.isCorrect){ playTone('correct'); speak(j.feedback.message || `Great!`, lang==='hindi' ? 'hi-IN' : 'en-US'); }
    else { playTone('incorrect'); speak(j.feedback.message || `Try again`, lang==='hindi' ? 'hi-IN' : 'en-US'); }
  }

  // show letters with spelling highlights and overlay confidences (if provided)
  function renderLettersRow(written, mistakes, correctFlag, confidences){
    const row = document.getElementById('letterRow'); row.innerHTML = '';
    const wrongByPos = {}; const missing = [];
    (mistakes||[]).forEach(m => {
      if(m.position_written !== null && m.position_written !== undefined) wrongByPos[m.position_written] = m;
      else if(m.position_correct !== null && m.position_correct !== undefined) missing.push(m.position_correct);
    });
    for(let i=0;i<written.length;i++){
      const ch = written[i];
      const el = document.createElement('span'); el.className='letter';
      // determine confidence color if available
      let conf = confidences && confidences[i] !== undefined ? confidences[i] : null;
      if(wrongByPos[i]){
        el.classList.add('wrong');
        el.title = wrongByPos[i].type + (wrongByPos[i].correct ? ' → '+wrongByPos[i].correct : '');
      } else {
        el.classList.add('correct');
      }
      el.textContent = ch;
      row.appendChild(el);
      // show confidence next to letter
      if(conf !== null){
        const cb = document.createElement('span');
        cb.className = 'confidence ' + (conf < 0.7 ? 'conf-low' : (conf < 0.8 ? 'conf-mid' : 'conf-high'));
        cb.textContent = ' ' + (conf*100).toFixed(0) + '%';
        row.appendChild(cb);
      }
    }
    missing.forEach(mp => {
      const el = document.createElement('span'); el.className='letter missing'; el.textContent='•'; el.title='Missing letter';
      if(mp >= row.children.length) row.appendChild(el); else row.insertBefore(el, row.children[mp]);
    });
    const fb = document.getElementById('kidFeedback'); fb.innerHTML = '';
    const msg = document.createElement('div'); msg.style.marginTop='8px';
    msg.innerHTML = correctFlag ? `<div class="ok">✅ Perfect! ${written}</div>` : `<div style="color:#b91c1c;font-weight:700">Almost! Try a suggestion below.</div>`;
    fb.appendChild(msg);
  }

  function renderHandwritingPanel(word, confidences){
    const panel = document.getElementById('handwritingPanel'); panel.innerHTML = '';
    if(!word){ panel.style.display='none'; return; }
    panel.style.display='block';
    const title = document.createElement('div'); title.style.marginBottom='6px'; title.innerHTML = '<strong>Handwriting recognizer (mock confidences)</strong>';
    panel.appendChild(title);
    const row = document.createElement('div');
    for(let i=0;i<word.length;i++){
      const ch = word[i];
      const conf = confidences[i];
      const box = document.createElement('div');
      box.style.display='inline-block'; box.style.marginRight='8px'; box.style.padding='6px'; box.style.borderRadius='8px';
      if(conf < 0.7){ box.style.background='#fff1f2'; box.style.border='1px solid #fecaca'; box.style.color='#9f1239'; }
      else if(conf < 0.8){ box.style.background='#fff7ed'; box.style.border='1px solid #fed7aa'; box.style.color='#92400e'; }
      else { box.style.background='#ecfdf5'; box.style.border='1px solid #bbf7d0'; box.style.color='#065f46'; }
      box.innerHTML = `<div style="font-weight:700;font-size:16px">${ch}</div><div style="font-size:12px;margin-top:4px">conf: ${(conf*100).toFixed(0)}%</div>`;
      row.appendChild(box);
    }
    panel.appendChild(row);
    const note = document.createElement('div'); note.className='muted'; note.style.marginTop='8px';
    note.textContent = 'Letters with low confidence are highlighted. In a real system, low-confidence letters could reduce suggestion confidence or trigger a re-prompt.';
    panel.appendChild(note);
  }

  function renderSuggestions(suggestions, feedback){
    const sdiv = document.getElementById('suggestions'); sdiv.innerHTML = '';
    if(suggestions && suggestions.length){
      suggestions.forEach(s => {
        const el = document.createElement('span'); el.className='suggestion'; el.textContent = s.word;
        el.write = () => { document.getElementById('kidInput').value = s.word; renderLettersRow(s.word, [], true, generateConfidences(s.word)); pronounce(s.word); };
        sdiv.appendChild(el);
      });
    } else { sdiv.innerHTML = `<div class="muted" style="margin-top:8px;">No suggestions</div>`; }
  }

  function generateConfidences(word){
    const confs = [];
    for(let i=0;i<word.length;i++){
      const v = Math.random() * 0.5 + 0.5; confs.push(Math.round(v*100)/100);
    }
    return confs;
  }

  async function analyzeLive(){
    const lettersRaw = document.getElementById('liveType').value.trim(); if(!lettersRaw){ alert('Type letters'); return; }
    const letters = lettersRaw.split(/\s+/);
    const res = await fetch('/api/v1/spelling/analyze-progress', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ lettersWritten: letters, expectedWord: "" })});
    const j = await res.json();
    const h = document.getElementById('liveHints'); h.innerHTML = `<div><strong>Progress:</strong> ${j.currentProgress} <strong>Remaining:</strong> ${j.remainingLetters ? j.remainingLetters.join('') : ''}</div>`;
    if(j.predictions && j.predictions.length){ const pred = j.predictions.map(p => `<span class="suggestion" onclick="fillWord('${p.word}')">${p.word}</span>`).join(' '); h.innerHTML += `<div style="margin-top:8px;"><strong>Predictions:</strong> ${pred}</div>`; }
  }

  function fillWord(w){ document.getElementById('kidInput').value = w; const confs = generateConfidences(w); renderLettersRow(w, [], true, confs); renderHandwritingPanel(w, confs); }

  function updateChartWith(points){
    if(!points || !points.length) return;
    const pt = points[points.length-1];
    const label = new Date(pt.ts*1000).toLocaleTimeString();
    chartData.labels.push(label);
    chartData.datasets[0].data.push(pt.accuracy);
    if(chartData.labels.length>40){ chartData.labels.shift(); chartData.datasets[0].data.shift(); }
    liveChart.update();
  }

  async function loadSession(){
    const s = await fetch('/api/v1/stats/session').then(r=>r.json());
    if(s.sessionPoints && s.sessionPoints.length){ s.sessionPoints.forEach(p => { chartData.labels.push(new Date(p.ts*1000).toLocaleTimeString()); chartData.datasets[0].data.push(p.accuracy); }); liveChart.update(); }
  }
  loadSession();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

def open_browser_later():
    try:
        webbrowser.open("http://127.0.0.1:5000")
    except Exception:
        pass

if __name__ == "__main__":
    print("Starting Effling Kids Spelling Demo at http://127.0.0.1:5000")
    t = threading.Timer(1.0, open_browser_later); t.daemon = True; t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
