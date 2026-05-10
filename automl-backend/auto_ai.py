import os, sys, json, time, warnings, argparse, glob
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from sklearn.experimental import enable_iterative_imputer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler, PowerTransformer
from sklearn.impute import SimpleImputer, KNNImputer, IterativeImputer
from sklearn.ensemble import IsolationForest
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report,
)
from sklearn.model_selection import RandomizedSearchCV
from imblearn.over_sampling import SMOTE

# ─── Load environment variables from .env ────────────────────────────────────
load_dotenv()

warnings.filterwarnings("ignore")
 
# ─── ANSI colours ─────────────────────────────────────────────────────────────
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
 
def banner(text, colour=CYAN):
    w = 64
    print(f"\n{colour}{BOLD}{'═'*w}\n  {text}\n{'═'*w}{RESET}")
 
def section(text): print(f"\n{BOLD}{CYAN}▶ {text}{RESET}")
def ok(text):      print(f"  {GREEN}✔  {text}{RESET}")
def warn(text):    print(f"  {YELLOW}⚠  {text}{RESET}")
def info(text):    print(f"  {DIM}{text}{RESET}")
def err(text):     print(f"  {RED}✖  {text}{RESET}")
def ask(prompt):   return input(f"\n{CYAN}{prompt}{RESET}").strip()
 
 
# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — Manual file upload from terminal
# ══════════════════════════════════════════════════════════════════════════════
 
SUPPORTED_EXT = {".csv", ".xlsx", ".xls", ".json"}
GROQ_MODELS   = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "llama3-8b-8192",
]
 
 
def _read_file(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[-1].lower()
    if ext not in SUPPORTED_EXT:
        raise ValueError(f"Unsupported format '{ext}'. Allowed: {SUPPORTED_EXT}")
    if ext == ".csv":
        for sep in [",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(path, sep=sep)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
        return pd.read_csv(path)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    elif ext == ".json":
        return pd.read_json(path)
 
 
def _prompt_file_path() -> str:
    print(f"\n  {DIM}Tip: enter the full or relative path to your file.{RESET}")
    print(f"  {DIM}Supported: CSV, Excel (.xlsx/.xls), JSON{RESET}")
    while True:
        raw = ask("  File path: ")
        if not raw:
            warn("No path given — try again.")
            continue
        path = os.path.expanduser(raw.strip('"').strip("'"))
        if not os.path.exists(path):
            hints = glob.glob(path + "*")
            if hints:
                print(f"  {DIM}Did you mean:{RESET}")
                for h in hints[:5]:
                    print(f"    {h}")
            else:
                err(f"File not found: {path}")
            continue
        if os.path.splitext(path)[-1].lower() not in SUPPORTED_EXT:
            err("Unsupported file type. Use CSV, Excel, or JSON.")
            continue
        return path
 
 
def _prompt_target_col(df: pd.DataFrame) -> str:
    print(f"\n  {BOLD}Columns in your dataset:{RESET}")
    for i, col in enumerate(df.columns, 1):
        null_pct = df[col].isnull().mean() * 100
        print(f"    [{i:>2}] {col:<30} {DIM}dtype={df[col].dtype}  "
              f"unique={df[col].nunique()}  null={null_pct:.1f}%{RESET}")
    while True:
        raw = ask("  Enter target column name or number: ")
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(df.columns):
                return df.columns[idx]
            err(f"Number out of range. Enter 1–{len(df.columns)}")
        elif raw in df.columns:
            return raw
        else:
            err(f"'{raw}' not found. Type the exact column name or its number.")
 
 
def load_dataset(file_path: str | None, target_col: str | None) -> tuple[pd.DataFrame, str]:
    banner("STAGE 1 — Load Dataset")
 
    # ── Resolve file path ──────────────────────────────────────────────────
    if file_path:
        path = os.path.expanduser(file_path)
        if not os.path.exists(path):
            err(f"File not found: {path}")
            sys.exit(1)
    else:
        path = _prompt_file_path()
 
    size_mb = os.path.getsize(path) / 1_048_576
    info(f"Reading: {path}  ({size_mb:.2f} MB)")
 
    try:
        df = _read_file(path)
    except Exception as exc:
        err(f"Could not read file: {exc}")
        sys.exit(1)
 
    if df.empty:
        err("Dataset is empty after loading.")
        sys.exit(1)
 
    ok(f"Loaded {df.shape[0]:,} rows × {df.shape[1]} columns")
 
    # ── Show preview ───────────────────────────────────────────────────────
    print(f"\n  {BOLD}Preview (first 4 rows):{RESET}")
    try:
        for line in df.head(4).to_string(max_cols=8, max_colwidth=16).split("\n"):
            print(f"  {line}")
    except Exception:
        print(df.head(4))
 
    print(f"\n  {BOLD}Column summary:{RESET}")
    for col in df.columns:
        null_pct = df[col].isnull().mean() * 100
        print(f"  {col:<30} {str(df[col].dtype):<12} "
              f"{DIM}null={null_pct:.1f}%  unique={df[col].nunique()}{RESET}")
 
    # ── Resolve target column ──────────────────────────────────────────────
    if target_col and target_col not in df.columns:
        err(f"Column '{target_col}' not found.")
        target_col = None
 
    if not target_col:
        target_col = _prompt_target_col(df)
 
    ok(f"Target: {BOLD}{target_col}{RESET}")
    info(f"Value counts: {df[target_col].value_counts().head(6).to_dict()}")
 
    # ── Detect task type ───────────────────────────────────────────────────
    nuniq = df[target_col].nunique()
    if nuniq == 2:
        task_hint = "binary classification"
    elif nuniq <= 20 and (df[target_col].dtype == object or nuniq < df.shape[0] * 0.05):
        task_hint = "multiclass classification"
    else:
        task_hint = "regression"
    ok(f"Detected task: {BOLD}{task_hint}{RESET}  ({nuniq} unique values in target)")
 
    return df, target_col
 
 
# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — Local statistical profiler (zero API cost, zero tokens)
# ══════════════════════════════════════════════════════════════════════════════
 
def build_profile(df: pd.DataFrame, target_col: str) -> dict:
    banner("STAGE 2 — Local Statistical Profiler")
 
    def safe(v):
        try:
            f = float(v)
            return None if (np.isnan(f) or np.isinf(f)) else round(f, 6)
        except Exception:
            return None
 
    profile = {
        "shape": {"rows": len(df), "cols": len(df.columns)},
        "global": {
            "total_null_cells": int(df.isnull().sum().sum()),
            "total_null_pct":   round(df.isnull().mean().mean() * 100, 2),
        },
        "columns": {},
    }
 
    for col in df.columns:
        s    = df[col]
        base = {
            "dtype":      str(s.dtype),
            "null_count": int(s.isnull().sum()),
            "null_pct":   round(s.isnull().mean() * 100, 2),
        }
 
        if pd.api.types.is_numeric_dtype(s):
            clean = s.dropna()
            if len(clean):
                q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
                iqr     = q3 - q1
                out_n   = int(((clean < q1-1.5*iqr) | (clean > q3+1.5*iqr)).sum())
                base.update({
                    "kind":         "numeric",
                    "mean":         safe(clean.mean()),
                    "std":          safe(clean.std()),
                    "min":          safe(clean.min()),
                    "max":          safe(clean.max()),
                    "skewness":     safe(scipy_stats.skew(clean)),
                    "kurtosis":     safe(scipy_stats.kurtosis(clean)),
                    "outlier_count": out_n,
                    "outlier_pct":  round(out_n / max(len(clean), 1) * 100, 2),
                    "zero_pct":     round((clean == 0).mean() * 100, 2),
                })
            else:
                base["kind"] = "numeric"
        else:
            vc       = s.value_counts()
            sample   = s.dropna().head(200)
            num_hit  = pd.to_numeric(sample, errors="coerce").notna().mean()
            base.update({
                "kind":             "categorical",
                "unique_count":     int(s.nunique()),
                "cardinality_ratio": round(s.nunique() / max(len(s), 1), 4),
                "top_values":       {str(k): int(v) for k, v in vc.head(5).items()},
                "looks_numeric":    bool(num_hit > 0.85),
            })
 
        if s.nunique() <= 1:
            base["constant"] = True
 
        profile["columns"][col] = base
 
    tgt = df[target_col]
    vc  = tgt.value_counts(normalize=True).round(4)
    profile["global"].update({
        "target_col":  target_col,
        "target_type": ("binary" if tgt.nunique() == 2
                        else "multiclass" if tgt.nunique() <= 20
                        else "regression"),
        "target_balance": {str(k): float(v) for k, v in vc.items()},
    })
    if vc.max() > 0.75:
        profile["global"]["severe_class_imbalance"] = True
 
    ok(f"Profiled {len(profile['columns'])} columns")
    info(f"Total nulls  : {profile['global']['total_null_cells']} ({profile['global']['total_null_pct']}%)")
    info(f"Target type  : {profile['global']['target_type']}")
    info(f"Balance      : {profile['global']['target_balance']}")
 
    return profile
 
 
# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — AI audit via Groq (sends profile JSON only, NOT raw data)
# ══════════════════════════════════════════════════════════════════════════════
 
AUDIT_SYSTEM_PROMPT = """You are a senior data scientist specialising in data quality assessment.
You receive a statistical profile of a dataset — no raw data rows are shared with you.
 
Return ONLY a valid JSON array. No markdown fences, no preamble, no explanation.
Each element must have exactly these keys:
{
  "id": "flag_NNN",
  "column": "<column name or 'global' for dataset-wide issues>",
  "issue_type": "<one of: missing_values | outliers | high_skew | class_imbalance | wrong_dtype | high_cardinality | constant_column | near_zero_variance | high_multicollinearity | distribution_anomaly>",
  "severity": "<high | medium | low>",
  "detail": "<one sentence: what the problem is and why it hurts ML>",
  "recommended_fix": "<specific technique e.g. 'Impute with IterativeImputer' or 'Apply Box-Cox transform' or 'Use RobustScaler'>",
  "auto_fixable": <true or false>
}
 
Severity: high=breaks/biases model, medium=degrades performance, low=best-practice.
Be thorough. Never merge two issues into one flag. Number ids: flag_000, flag_001 ...
Available fixes:
  - Imputation: 'IterativeImputer' (best for correlated missing), 'KNN imputation', 'mean', 'median', 'most_frequent'
  - Outliers: 'Isolation Forest', 'IQR clipping', 'Z-score clipping'
  - Scaling: 'RobustScaler' (for outliers), 'StandardScaler'
  - Transforms: 'Box-Cox transform' (normalization), 'log1p transform', 'Yeo-Johnson transform'
  - Multicollinearity: 'Remove high-VIF features' (VIF > 10)
If the dataset looks clean, return [].
"""
 
 
def run_ai_audit(profile: dict, groq_model: str | None = None) -> list[dict]:
    banner("STAGE 3 — AI Audit (Groq API)")
 
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        err("GROQ_API_KEY not set.")
        print(f"\n  Set it with:  export GROQ_API_KEY=gsk_...")
        sys.exit(1)
 
    from groq import Groq
    client = Groq(api_key=api_key)
 
    # Strip sample_values to minimise tokens
    import copy
    p = copy.deepcopy(profile)
    for cd in p.get("columns", {}).values():
        cd.pop("sample_values", None)
 
    profile_str = json.dumps(p, indent=2, default=str)
    est_tokens  = (len(profile_str) + len(AUDIT_SYSTEM_PROMPT)) // 4
 
    info(f"Profile size : {len(profile_str):,} chars (~{est_tokens:,} tokens)")
    info(f"Raw data     : NOT sent — stats only")
    info(f"Cost         : $0.00  (Groq free tier)")
 
    # Pick model; fall back through list on rate-limit / unavailability
    model    = groq_model or GROQ_MODELS[0]
    fallback = [m for m in GROQ_MODELS if m != model]
    info(f"Model        : {model}")
 
    t0, last_exc = time.time(), None
    for attempt in ([model] + fallback):
        try:
            response = client.chat.completions.create(
                model=attempt,
                messages=[
                    {"role": "system", "content": AUDIT_SYSTEM_PROMPT},
                    {"role": "user",   "content": f"Audit this dataset profile:\n\n{profile_str}"},
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            model = attempt
            break
        except Exception as exc:
            warn(f"  {attempt} → {exc}. Trying next model...")
            last_exc = exc
    else:
        err(f"All Groq models failed. Last: {last_exc}")
        sys.exit(1)
 
    elapsed = round(time.time() - t0, 2)
    raw     = response.choices[0].message.content.strip()
 
    # Strip markdown fences if any
    if "```" in raw:
        for part in raw.split("```"):
            cleaned = part.strip().lstrip("json").strip()
            if cleaned.startswith("["):
                raw = cleaned
                break
 
    # Parse JSON
    try:
        flags = json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("["), raw.rfind("]") + 1
        if s != -1 and e > s:
            flags = json.loads(raw[s:e])
        else:
            err("Could not parse Groq response as JSON.")
            print(f"  Raw (first 600 chars):\n{raw[:600]}")
            sys.exit(1)
 
    for i, f in enumerate(flags):
        f.setdefault("id", f"flag_{i:03d}")
 
    u = response.usage
    ok(f"Audit done in {elapsed}s  |  model: {model}")
    info(f"Tokens: {u.prompt_tokens} in / {u.completion_tokens} out  (Groq — FREE)")
    ok(f"{len(flags)} data quality flags returned")
    return flags
 
 
# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — User reviews flags in terminal
# ══════════════════════════════════════════════════════════════════════════════
 
SEV_COL = {"high": RED, "medium": YELLOW, "low": GREEN}
 
 
def user_review_flags(flags: list[dict]) -> list[dict]:
    banner("STAGE 4 — Review AI Flags")
 
    if not flags:
        ok("No issues found — dataset looks clean!")
        return []
 
    high   = [f for f in flags if f["severity"] == "high"]
    medium = [f for f in flags if f["severity"] == "medium"]
    low    = [f for f in flags if f["severity"] == "low"]
 
    print(f"  Total: {BOLD}{len(flags)} flags{RESET}   "
          f"{RED}high={len(high)}{RESET}  "
          f"{YELLOW}medium={len(medium)}{RESET}  "
          f"{GREEN}low={len(low)}{RESET}\n")
 
    for f in flags:
        sc   = SEV_COL.get(f["severity"], RESET)
        fix_m = f"{GREEN}✦ AUTO{RESET}" if f.get("auto_fixable") else f"{DIM}manual{RESET}"
        print(f"  {sc}{BOLD}[{f['severity'].upper():6}]{RESET}  "
              f"{BOLD}{f['id']}{RESET}  col={f['column']!r}")
        print(f"           type  : {f['issue_type']}")
        print(f"           detail: {f['detail']}")
        print(f"           fix   : {f['recommended_fix']}  ({fix_m})")
        print()
 
    print(f"{BOLD}  Confirm fixes:{RESET}")
    print("    [1] Accept ALL flags               (recommended)")
    print("    [2] Accept HIGH + MEDIUM only")
    print("    [3] Accept only auto-fixable flags")
    print("    [4] Choose by flag ID manually")
    print("    [5] Skip all fixes")
 
    choice = ask("  Choice (1-5) [default=1]: ") or "1"
 
    if choice == "1":
        confirmed = flags
    elif choice == "2":
        confirmed = [f for f in flags if f["severity"] in ("high", "medium")]
    elif choice == "3":
        confirmed = [f for f in flags if f.get("auto_fixable")]
    elif choice == "4":
        ids_str = ask("  Flag IDs to accept (comma-separated, e.g. flag_000,flag_002): ")
        chosen  = {x.strip() for x in ids_str.split(",") if x.strip()}
        confirmed = [f for f in flags if f["id"] in chosen]
        invalid   = chosen - {f["id"] for f in flags}
        if invalid:
            warn(f"Unknown IDs ignored: {invalid}")
    elif choice == "5":
        confirmed = []
    else:
        confirmed = flags
 
    ok(f"Confirmed {len(confirmed)} / {len(flags)} flags for automated fixing")
    return confirmed
 
 
# ══════════════════════════════════════════════════════════════════════════════
# STAGE 5 — Automated preprocessing
# ══════════════════════════════════════════════════════════════════════════════
 
def apply_preprocessing(df: pd.DataFrame, confirmed: list[dict], target_col: str) -> tuple[pd.DataFrame, list[str]]:
    banner("STAGE 5 — Automated Preprocessing")
    log = []
 
    def _impute(s: pd.Series, strategy: str) -> pd.Series:
        if strategy == "iterative":
            imp = IterativeImputer(max_iter=10, random_state=42, verbose=0)
            return pd.Series(imp.fit_transform(s.to_frame())[:, 0], index=s.index, name=s.name)
        elif strategy == "knn":
            imp = KNNImputer(n_neighbors=5)
            return pd.Series(imp.fit_transform(s.to_frame())[:, 0], index=s.index, name=s.name)
        imp = SimpleImputer(strategy=strategy)
        return pd.Series(imp.fit_transform(s.to_frame())[:, 0], index=s.index, name=s.name)
 
    for flag in confirmed:
        col   = flag["column"]
        issue = flag["issue_type"]
        fix   = flag.get("recommended_fix", "").lower()
        try:
            # ── Global / dataset-wide ──────────────────────────────────
            if col == "global":
                if issue == "class_imbalance":
                    log.append("class_imbalance: SMOTE scheduled after split")
                    info("SMOTE will run after train/test split")
                continue
 
            if col not in df.columns:
                warn(f"Column '{col}' not in dataframe — skipped"); continue
 
            # ── Per-column ─────────────────────────────────────────────
            if issue == "missing_values":
                if col == target_col:
                    before = len(df)
                    df     = df.dropna(subset=[col])
                    msg    = f"{col}: dropped {before-len(df)} rows with null target"
                else:
                    strat = ("iterative"     if "iterative" in fix
                             else "knn"      if "knn"       in fix
                             else "mean"     if "mean"      in fix
                             else "most_frequent" if ("mode" in fix or "frequent" in fix)
                             else "median"   if pd.api.types.is_numeric_dtype(df[col])
                             else "most_frequent")
                    df[col] = _impute(df[col], strat)
                    msg = f"{col}: nulls imputed using {strat}"
                ok(msg); log.append(msg)
 
            elif issue == "outliers":
                method = ("isolation_forest" if "isolation" in fix
                         else "zscore" if "zscore" in fix or "z-score" in fix
                         else "iqr")
                if method == "isolation_forest":
                    iso = IsolationForest(contamination=0.05, random_state=42)
                    outlier_mask = iso.fit_predict(df[[col]].fillna(df[col].median())) == -1
                    df.loc[outlier_mask, col] = df.loc[~outlier_mask, col].median()
                    msg = f"{col}: outliers isolated & replaced ({method})"
                elif method == "iqr":
                    q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
                    df[col] = df[col].clip(q1 - 1.5*(q3-q1), q3 + 1.5*(q3-q1))
                    msg = f"{col}: outliers clipped ({method.upper()})"
                else:
                    m, s = df[col].mean(), df[col].std()
                    df[col] = df[col].clip(m - 3*s, m + 3*s)
                    msg = f"{col}: outliers clipped ({method.upper()})"
                ok(msg); log.append(msg)
 
            elif issue == "high_skew":
                transform = "yeo_johnson" if "yeo-johnson" in fix or "yeo_johnson" in fix else "log1p"
                if transform == "yeo_johnson":
                    pt = PowerTransformer(method="yeo-johnson")
                    df[col] = pt.fit_transform(df[[col]])
                    msg = f"{col}: Yeo-Johnson transform applied (handles all ranges)"
                else:
                    shift   = max(0.0, -df[col].min() + 1) if df[col].min() <= 0 else 0.0
                    df[col] = np.log1p(df[col] + shift)
                    msg = f"{col}: log1p applied (shift={shift:.2f})"
                ok(msg); log.append(msg)

            elif issue == "distribution_anomaly":
                # Use PowerTransformer (Yeo-Johnson) for robust distribution normalization
                try:
                    pt = PowerTransformer(method="yeo-johnson", standardize=True)
                    df[col] = pt.fit_transform(df[[col]])
                    msg = f"{col}: Yeo-Johnson distribution normalization applied"
                    ok(msg); log.append(msg)
                except Exception as e:
                    warn(f"{col}: Could not apply distribution transform: {e}")
 
            elif issue == "wrong_dtype":
                if "numeric" in fix or "float" in fix or "int" in fix:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    msg = f"{col}: cast to numeric"
                elif "date" in fix:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    msg = f"{col}: cast to datetime"
                else:
                    msg = f"{col}: dtype flag noted (no clear target type)"
                ok(msg); log.append(msg)
 
            elif issue == "constant_column":
                if col != target_col:
                    df  = df.drop(columns=[col])
                    msg = f"{col}: dropped (constant — zero predictive value)"
                    ok(msg); log.append(msg)
 
            elif issue == "high_cardinality":
                if col != target_col and df[col].dtype == object:
                    n = df[col].nunique()
                    if n <= 15:
                        dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
                        df      = pd.concat([df.drop(columns=[col]), dummies], axis=1)
                        msg     = f"{col}: one-hot encoded ({n} cats)"
                    else:
                        df[col] = LabelEncoder().fit_transform(df[col].astype(str))
                        msg     = f"{col}: label encoded ({n} cats)"
                    ok(msg); log.append(msg)
 
            elif issue == "class_imbalance":
                log.append("class_imbalance: SMOTE scheduled after split")
                info("SMOTE will run after train/test split")

            elif issue == "high_multicollinearity":
                if col != target_col and col in df.columns:
                    df = df.drop(columns=[col])
                    msg = f"{col}: dropped (high VIF > 10 — multicollinearity)"
                    ok(msg); log.append(msg)
 
        except Exception as exc:
            err(f"Error on '{col}' ({issue}): {exc}")
            log.append(f"ERROR: {col} ({issue}): {exc}")
 
    # ── Auto-encode remaining object columns ───────────────────────────────
    for col in df.select_dtypes(include=["object", "category"]).columns:
        if col == target_col:
            continue
        n = df[col].nunique()
        if n <= 15:
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
            df      = pd.concat([df.drop(columns=[col]), dummies], axis=1)
            msg     = f"{col}: auto one-hot encoded ({n} cats)"
        else:
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))
            msg     = f"{col}: auto label encoded ({n} cats)"
        ok(msg); log.append(msg)
 
    # ── Drop datetime columns (sklearn can't use raw datetimes) ───────────
    for col in df.select_dtypes(include=["datetime64"]).columns:
        if col == target_col:
            continue
        df  = df.drop(columns=[col])
        msg = f"{col}: datetime dropped (convert to numeric features manually if needed)"
        warn(msg); log.append(msg)
 
    # ── Standard-scale numeric features ───────────────────────────────────
    num_cols = [c for c in df.select_dtypes(include="number").columns if c != target_col]
    if num_cols:
        # Check for high skewness or outliers to choose scaler
        use_robust = False
        for col in num_cols:
            skewness = scipy_stats.skew(df[col].dropna())
            if abs(skewness) > 1.5:  # High skewness
                use_robust = True
                break
        
        if use_robust:
            df[num_cols] = RobustScaler().fit_transform(df[num_cols])
            msg = f"RobustScaler applied to {len(num_cols)} numeric columns (skewed/outlier-heavy)"
        else:
            df[num_cols] = StandardScaler().fit_transform(df[num_cols])
            msg = f"StandardScaler applied to {len(num_cols)} numeric columns"
        ok(msg); log.append(msg)
 
    print(f"\n  {BOLD}Clean shape : {df.shape}{RESET}")
    info(f"Remaining nulls : {df.isnull().sum().sum()}")
    return df, log
 
 
# ══════════════════════════════════════════════════════════════════════════════
# STAGE 6 — Feature engineering + train/test split
# ══════════════════════════════════════════════════════════════════════════════

def _calculate_vif(df_numeric):
    """Calculate Variance Inflation Factor for each numeric column."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    vif_data = pd.DataFrame()
    vif_data["Feature"] = df_numeric.columns
    vif_data["VIF"] = [variance_inflation_factor(df_numeric.values, i) 
                       for i in range(df_numeric.shape[1])]
    return vif_data


 
def run_feature_engineering(df: pd.DataFrame, target_col: str, confirmed: list[dict]) -> tuple:
    banner("STAGE 6 — Feature Engineering & Split")
 
    X = df.drop(columns=[target_col])
    y = df[target_col]
 
    # Fill any residual NaNs before sklearn
    for col in X.columns:
        if X[col].isnull().any():
            fill = X[col].median() if pd.api.types.is_numeric_dtype(X[col]) else X[col].mode().iloc[0]
            X[col] = X[col].fillna(fill)
 
    task_type = "classification" if y.nunique() <= 20 else "regression"
    y_enc = LabelEncoder().fit_transform(y) if y.dtype == object else y.values
 
    # ── Importance probe ───────────────────────────────────────────────────
    probe = RandomForestClassifier(n_estimators=80, random_state=42, n_jobs=-1) \
        if task_type == "classification" else \
        __import__("sklearn.ensemble", fromlist=["RandomForestRegressor"]).RandomForestRegressor(
            n_estimators=80, random_state=42, n_jobs=-1)
    probe.fit(X, y_enc)
 
    imp = pd.Series(probe.feature_importances_, index=X.columns).sort_values(ascending=False)
 
    print(f"\n  {BOLD}Feature Importance (top 12):{RESET}")
    for feat, score in imp.head(12).items():
        bar = "█" * int(score * 200)
        print(f"  {str(feat):<32} {score:.4f}  {GREEN}{bar}{RESET}")
 
    # ── High-correlation warning ───────────────────────────────────────────
    num_cols = X.select_dtypes(include="number").columns.tolist()
    if len(num_cols) > 1:
        corr  = X[num_cols].corr().abs()
        pairs = [(corr.columns[i], corr.columns[j], round(float(corr.iloc[i,j]),4))
                 for i in range(len(corr.columns))
                 for j in range(i+1, len(corr.columns))
                 if corr.iloc[i,j] >= 0.88]
        if pairs:
            warn("High-correlation pairs (≥0.88):")
            for a, b, v in pairs:
                info(f"  {a}  ↔  {b}  :  {v}")
    
    # ── VIF Detection for multicollinearity ────────────────────────────────
    try:
        if len(num_cols) > 2:
            vif_df = _calculate_vif(X[num_cols])
            high_vif = vif_df[vif_df["VIF"] > 10].sort_values("VIF", ascending=False)
            if len(high_vif) > 0:
                warn(f"High VIF features detected (VIF > 10):")
                for _, row in high_vif.iterrows():
                    info(f"  {row['Feature']:<32} VIF={row['VIF']:.2f}")
                    if row['Feature'] in X.columns:
                        X = X.drop(columns=[row['Feature']])
                        info(f"    → Removed due to high multicollinearity")
    except Exception as e:
        info(f"VIF calculation skipped: {e}")
    
 
    # ── Select features covering 98% cumulative importance ────────────────
    keep = imp.cumsum()[imp.cumsum() <= 0.98].index.tolist()
    if len(keep) < 2:
        keep = imp.index[:max(2, len(imp))].tolist()
    X    = X[keep]
    ok(f"Selected {len(keep)} features (≥98% cumulative importance)")
 
    # ── Split ──────────────────────────────────────────────────────────────
    strat = y if task_type == "classification" else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=strat)
 
    # ── SMOTE ─────────────────────────────────────────────────────────────
    if any(f["issue_type"] == "class_imbalance" for f in confirmed) and task_type == "classification":
        # Ensure zero NaNs
        for col in X_train.columns:
            if X_train[col].isnull().any():
                fill = X_train[col].median() if pd.api.types.is_numeric_dtype(X_train[col]) else 0
                X_train[col] = X_train[col].fillna(fill)
                X_test[col]  = X_test[col].fillna(fill)
 
        y_tr_enc = LabelEncoder().fit_transform(y_train) if y_train.dtype == object else y_train
        X_res, y_res = SMOTE(random_state=42).fit_resample(X_train, y_tr_enc)
        X_train = pd.DataFrame(X_res, columns=X_train.columns)
        y_train = pd.Series(y_res, name=y_train.name)
        ok(f"SMOTE → train {X_train.shape[0]} rows  balance: {pd.Series(y_train).value_counts().to_dict()}")
    else:
        info("SMOTE not applied")
 
    ok(f"Train: {len(X_train):,} rows  |  Test: {len(X_test):,} rows")
    return X_train, X_test, y_train, y_test, keep, task_type
 
 
# ══════════════════════════════════════════════════════════════════════════════
# STAGE 7 — Model training with hyperparameter tuning
# ══════════════════════════════════════════════════════════════════════════════
 
REGISTRY = {
    "logistic_regression": {
        "model":  LogisticRegression(max_iter=1000, random_state=42),
        "params": {"C": [0.01, 0.1, 1, 10, 100], "solver": ["lbfgs", "liblinear"]},
    },
    "random_forest": {
        "model":  RandomForestClassifier(random_state=42, n_jobs=-1),
        "params": {
            "n_estimators": [100, 200, 300],
            "max_depth":    [None, 5, 10, 20],
            "min_samples_split": [2, 5, 10],
        },
    },
    "gradient_boosting": {
        "model":  GradientBoostingClassifier(random_state=42),
        "params": {
            "n_estimators":  [100, 150, 200],
            "learning_rate": [0.05, 0.1, 0.2],
            "max_depth":     [3, 5, 7],
        },
    },
    "knn": {
        "model":  KNeighborsClassifier(n_jobs=-1),
        "params": {"n_neighbors": [3, 5, 7, 11, 15], "weights": ["uniform", "distance"]},
    },
    "svm": {
        "model":  SVC(probability=True, random_state=42),
        "params": {"C": [0.1, 1, 10], "kernel": ["rbf", "linear"]},
    },
    "mlp": {
        "model":  MLPClassifier(max_iter=500, random_state=42),
        "params": {
            "hidden_layer_sizes": [(64,), (128,), (64, 32), (128, 64)],
            "activation":         ["relu", "tanh"],
            "alpha":              [0.0001, 0.001],
        },
    },
}
 
try:
    from xgboost import XGBClassifier
    REGISTRY["xgboost"] = {
        "model":  XGBClassifier(random_state=42, eval_metric="logloss", verbosity=0),
        "params": {
            "n_estimators":  [100, 200, 300],
            "learning_rate": [0.05, 0.1, 0.2],
            "max_depth":     [3, 5, 7],
            "subsample":     [0.8, 1.0],
        },
    }
except ImportError:
    pass
 
try:
    from lightgbm import LGBMClassifier
    REGISTRY["lightgbm"] = {
        "model":  LGBMClassifier(random_state=42, verbose=-1),
        "params": {
            "n_estimators":  [100, 200, 300],
            "learning_rate": [0.05, 0.1, 0.2],
            "num_leaves":    [31, 63, 127],
        },
    }
except ImportError:
    pass
 
 
def choose_models(task_type: str) -> list[str]:
    banner("STAGE 7 — Model Selection")
    names = list(REGISTRY.keys())
 
    print(f"  {BOLD}Task: {task_type}{RESET}\n")
    print(f"  {BOLD}Available models:{RESET}")
    for i, n in enumerate(names, 1):
        print(f"    [{i}] {n}")
 
    print(f"\n  {BOLD}Quick options:{RESET}")
    print("    [a] Train ALL models")
    print("    [b] Quick: logistic + random_forest + xgboost  (default)")
    print("    [#] Numbers, e.g.  1,3,6")
 
    choice = ask("  Choice [default=b]: ").lower() or "b"
 
    if choice == "a":
        return names
    elif choice == "b":
        defaults = ["logistic_regression", "random_forest"]
        if "xgboost" in REGISTRY:
            defaults.append("xgboost")
        return defaults
    else:
        try:
            idxs   = [int(x.strip()) - 1 for x in choice.split(",")]
            chosen = [names[i] for i in idxs if 0 <= i < len(names)]
            return chosen or ["logistic_regression", "random_forest"]
        except Exception:
            return ["logistic_regression", "random_forest"]
 
 
def train_models(model_names: list[str], X_train, y_train, n_iter=15, cv=5) -> dict:
    banner("Training Models")
    results = {}
 
    y_enc = LabelEncoder().fit_transform(y_train) if y_train.dtype == object else y_train.values
 
    for name in model_names:
        if name not in REGISTRY:
            warn(f"'{name}' not in registry — skipped"); continue
 
        entry  = REGISTRY[name]
        params = entry["params"]
        info(f"\nTraining {BOLD}{name}{RESET}...")
        t0 = time.time()
 
        if params:
            n_comb  = 1
            for v in params.values():
                n_comb *= len(v)
            search = RandomizedSearchCV(
                entry["model"], params,
                n_iter=min(n_iter, n_comb),
                cv=cv, scoring="f1_weighted",
                random_state=42, n_jobs=-1, refit=True,
            )
            search.fit(X_train, y_enc)
            best        = search.best_estimator_
            best_params = search.best_params_
        else:
            best = entry["model"]
            best.fit(X_train, y_enc)
            best_params = {}
 
        cv_scores = cross_val_score(best, X_train, y_enc, cv=cv, scoring="f1_weighted", n_jobs=-1)
        elapsed   = round(time.time() - t0, 2)
 
        ok(f"{name}: CV F1 = {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}  [{elapsed}s]")
        if best_params:
            info(f"  Best params : {best_params}")
        
        # ── Detect and handle overfitting/underfitting ───────────────────
        train_score = cross_val_score(best, X_train, y_enc, cv=2, scoring="f1_weighted").mean()
        cv_mean = np.mean(cv_scores)
        gap = abs(train_score - cv_mean)
        
        # More sensitive overfitting detection: test > CV or near-perfect scores
        if (train_score > cv_mean + 0.10) or (cv_mean >= 0.98 and train_score > cv_mean):
            warn(f"  ⚠ OVERFITTING detected (train-CV gap: {gap:.4f}, train={train_score:.4f}, cv={cv_mean:.4f})")
            info(f"  Applying regularization to reduce overfitting...")
            
            # Create regularized version of the model
            if name == "random_forest":
                best = RandomForestClassifier(
                    n_estimators=100, max_depth=10, min_samples_split=20,
                    min_samples_leaf=10, random_state=42, n_jobs=-1)
                best.fit(X_train, y_enc)
                ok(f"  ✓ Random Forest re-tuned (max_depth=10, higher min_samples)")
            elif name == "gradient_boosting":
                best = GradientBoostingClassifier(
                    n_estimators=100, learning_rate=0.05, max_depth=3,
                    subsample=0.8, random_state=42)
                best.fit(X_train, y_enc)
                ok(f"  ✓ Gradient Boosting re-tuned (lower learning_rate, max_depth=3)")
            elif name == "xgboost":
                try:
                    from xgboost import XGBClassifier
                    best = XGBClassifier(
                        n_estimators=100, learning_rate=0.05, max_depth=4,
                        subsample=0.8, colsample_bytree=0.8, reg_alpha=1.0,
                        reg_lambda=1.0, random_state=42, eval_metric="logloss", verbosity=0)
                    best.fit(X_train, y_enc)
                    ok(f"  ✓ XGBoost re-tuned (L1/L2 regularization added)")
                except ImportError:
                    pass
            elif name == "mlp":
                best = MLPClassifier(
                    hidden_layer_sizes=(64,), activation="relu", alpha=0.01,
                    max_iter=500, early_stopping=True, validation_fraction=0.1,
                    random_state=42)
                best.fit(X_train, y_enc)
                ok(f"  ✓ MLP re-tuned (higher alpha regularization, early stopping)")
            elif name == "logistic_regression":
                best = LogisticRegression(C=0.1, solver="lbfgs", max_iter=1000, random_state=42)
                best.fit(X_train, y_enc)
                ok(f"  ✓ Logistic Regression re-tuned (C=0.1 for stronger regularization)")
            
            # If still overfitting after regularization, warn user
            if cv_mean >= 0.98:
                warn(f"  ⚠⚠ SEVERE OVERFITTING: CV score is exceptionally high ({cv_mean:.4f})")
                info(f"  → Check for data leakage (target information in features)")
                info(f"  → Verify train/test split is truly independent")
                info(f"  → Consider removing highly predictive features that may cause leakage")
            
            # Recalculate CV scores after regularization
            cv_scores = cross_val_score(best, X_train, y_enc, cv=cv, scoring="f1_weighted", n_jobs=-1)
            elapsed = round(time.time() - t0, 2)
        
        elif cv_mean - train_score > 0.08:  # Underfitting: CV better than train
            warn(f"  ⚠ UNDERFITTING detected (CV-train gap: {cv_mean - train_score:.4f})")
            info(f"  Increasing model complexity...")
            
            # Create more complex version of the model
            if name == "random_forest":
                best = RandomForestClassifier(
                    n_estimators=300, max_depth=20, min_samples_split=2,
                    min_samples_leaf=1, random_state=42, n_jobs=-1)
                best.fit(X_train, y_enc)
                ok(f"  ✓ Random Forest enhanced (increased depth & estimators)")
            elif name == "gradient_boosting":
                best = GradientBoostingClassifier(
                    n_estimators=200, learning_rate=0.1, max_depth=7,
                    subsample=1.0, random_state=42)
                best.fit(X_train, y_enc)
                ok(f"  ✓ Gradient Boosting enhanced (higher learning_rate & depth)")
            elif name == "logistic_regression":
                best = LogisticRegression(C=100, solver="lbfgs", max_iter=1000, random_state=42)
                best.fit(X_train, y_enc)
                ok(f"  ✓ Logistic Regression enhanced (C=100 for less regularization)")
            elif name == "mlp":
                best = MLPClassifier(
                    hidden_layer_sizes=(128, 64), activation="relu", alpha=0.0001,
                    max_iter=1000, random_state=42)
                best.fit(X_train, y_enc)
                ok(f"  ✓ MLP enhanced (deeper layers, lower regularization)")
            
            # Recalculate CV scores after complexity increase
            cv_scores = cross_val_score(best, X_train, y_enc, cv=cv, scoring="f1_weighted", n_jobs=-1)
            elapsed = round(time.time() - t0, 2)
 
        results[name] = {
            "model":             best,
            "best_params":       best_params,
            "cv_scores":         cv_scores.tolist(),
            "cv_mean":           round(float(np.mean(cv_scores)), 4),
            "cv_std":            round(float(np.std(cv_scores)), 4),
            "training_time_sec": elapsed,
        }
 
    return results
 
 
# ══════════════════════════════════════════════════════════════════════════════
# STAGE 8 — Evaluation
# ══════════════════════════════════════════════════════════════════════════════
 
def _bar(v: float, w: int = 28) -> str:
    v = max(0.0, min(1.0, float(v)))
    return f"{GREEN}{'█'*int(v*w)}{DIM}{'░'*(w-int(v*w))}{RESET} {v:.4f}"
 
 
def _print_cm(cm, labels):
    print(f"\n  {BOLD}Confusion Matrix:{RESET}  (rows=actual, cols=predicted)")
    ls  = [str(l) for l in labels]
    cw  = max(max(len(s) for s in ls), 5) + 2
    hdr = " " * (cw + 4) + "  ".join(f"{l:>{cw}}" for l in ls)
    print(f"  {hdr}")
    for i, row in enumerate(cm):
        cells = "  ".join(
            f"{GREEN if i==j else DIM}{v:>{cw}}{RESET}" for j, v in enumerate(row))
        print(f"  {ls[i]:>{cw}} │ {cells}")
 
 
def _print_cv(scores, name):
    print(f"\n  {BOLD}Cross-Validation — {name}:{RESET}")
    mean, std = np.mean(scores), np.std(scores)
    for i, s in enumerate(scores, 1):
        marker = f"  {DIM}◀ best{RESET}" if s == max(scores) else ""
        print(f"  Fold {i}: {_bar(s)}{marker}")
    col = GREEN if mean >= 0.8 else YELLOW if mean >= 0.6 else RED
    print(f"  {col}{BOLD}  Mean={mean:.4f}   Std={std:.4f}{RESET}")
 
 
def _ascii_roc(fpr_l, tpr_l, auc_val):
    H, W = 9, 46
    grid = [["·"] * W for _ in range(H)]
    for fp, tp in zip(fpr_l, tpr_l):
        x = min(int(fp * W), W-1)
        y = min(int((1-tp) * H), H-1)
        grid[y][x] = f"{GREEN}*{RESET}"
    print(f"\n  {BOLD}ROC Curve — AUC = {auc_val:.4f}:{RESET}")
    print(f"  TPR")
    print(f"  1.0 ┐")
    for row in grid:
        print(f"      │ {''.join(row)}")
    print(f"  0.0 └{'─'*W}▶ FPR  1.0")
 
 
def evaluate_all(trained: dict, X_test, y_test, X_train, y_train) -> dict:
    banner("STAGE 8 — Evaluation Dashboard")
    results = {}
 
    le = None
    if y_test.dtype == object:
        le = LabelEncoder().fit(pd.concat([y_train, y_test]))
 
    for name, res in trained.items():
        model = res["model"]
        section(f"Model: {BOLD}{name}{RESET}")
 
        y_te  = le.transform(y_test) if le else y_test.values
        y_tr  = le.transform(y_train) if le else y_train.values
        y_pr  = model.predict(X_test)
        y_pr_train = model.predict(X_train)
        if le and y_pr.dtype == object:
            y_pr = le.transform(y_pr)
        if le and y_pr_train.dtype == object:
            y_pr_train = le.transform(y_pr_train)
        classes = np.unique(np.concatenate([y_te, y_pr]))
 
        # Calculate all three metrics: train, test, CV
        train_acc = accuracy_score(y_tr, y_pr_train)
        test_acc  = accuracy_score(y_te, y_pr)
        cv_mean   = res["cv_mean"]
        
        # Key gaps for overfitting diagnosis
        train_test_gap = abs(train_acc - test_acc)  # Primary indicator
        test_cv_gap    = abs(test_acc - cv_mean)
        
        acc  = test_acc
        f1   = f1_score(y_te, y_pr, average="weighted", zero_division=0)
        prec = precision_score(y_te, y_pr, average="weighted", zero_division=0)
        rec  = recall_score(y_te, y_pr, average="weighted", zero_division=0)
        
        # Detect overfitting/underfitting using TRAIN-TEST gap (primary metric)
        print(f"\n  {BOLD}Generalization Analysis:{RESET}")
        print(f"  Train Acc : {train_acc:.4f}")
        print(f"  Test Acc  : {test_acc:.4f}   (train-test gap: {train_test_gap:.4f})")
        print(f"  CV Mean   : {cv_mean:.4f}   (test-CV gap: {test_cv_gap:.4f})")
        
        # Overfitting: train >> test (memorization is real problem)
        if train_test_gap > 0.15:  # 15%+ gap indicates memorization
            warn(f"  ⚠ OVERFITTING DETECTED: Train({train_acc:.4f}) >> Test({test_acc:.4f})")
            info(f"  → Model memorized training data; performance degrades on unseen data")
        # Underfitting: model struggles on both train and test
        elif train_acc < 0.60 and test_acc < 0.65:
            warn(f"  ⚠ UNDERFITTING: Both train({train_acc:.4f}) and test({test_acc:.4f}) are weak")
            info(f"  → Model lacks complexity; add features or increase model capacity")
        # Excellent generalization: all three close together
        elif (abs(train_acc - test_acc) < 0.05 and 
              abs(test_acc - cv_mean) < 0.05 and 
              test_acc >= 0.85):
            ok(f"  ✔ EXCELLENT GENERALIZATION")
            info(f"  → Train≈Test≈CV: all excellent, model generalizes perfectly")
        # Good generalization
        elif train_test_gap < 0.10:
            ok(f"  ✔ GOOD GENERALIZATION: Train-Test gap={train_test_gap:.4f} (acceptable)")
            info(f"  → Model performs consistently on train and test data")
        else:
            ok(f"  ✔ BALANCED: Train-Test gap={train_test_gap:.4f}")
            info(f"  → Model shows reasonable generalization")
 
        print(f"\n  {BOLD}Core Metrics:{RESET}")
        print(f"  {'Accuracy':<22} {_bar(acc)}")
        print(f"  {'F1  (weighted)':<22} {_bar(f1)}")
        print(f"  {'Precision':<22} {_bar(prec)}")
        print(f"  {'Recall':<22} {_bar(rec)}")
 
        roc_auc_val = None
        if hasattr(model, "predict_proba"):
            try:
                y_prob = model.predict_proba(X_test)
                if len(classes) == 2:
                    roc_auc_val = roc_auc_score(y_te, y_prob[:, 1])
                    fpr, tpr, _ = roc_curve(y_te, y_prob[:, 1])
                    print(f"  {'ROC-AUC':<22} {_bar(roc_auc_val)}")
                    step = max(1, len(fpr) // 60)
                    _ascii_roc(fpr[::step].tolist(), tpr[::step].tolist(), roc_auc_val)
                else:
                    from sklearn.preprocessing import label_binarize
                    roc_auc_val = roc_auc_score(
                        label_binarize(y_te, classes=classes), y_prob,
                        multi_class="ovr", average="weighted")
                    print(f"  {'ROC-AUC (OvR)':<22} {_bar(roc_auc_val)}")
            except Exception as exc:
                warn(f"ROC-AUC skipped: {exc}")
 
        _print_cm(confusion_matrix(y_te, y_pr), classes)
        _print_cv(res["cv_scores"], name)
 
        if hasattr(model, "feature_importances_"):
            fi  = pd.Series(model.feature_importances_, index=X_test.columns).sort_values(ascending=False)
            print(f"\n  {BOLD}Top 8 Feature Importances:{RESET}")
            for feat, score in fi.head(8).items():
                print(f"  {str(feat):<32} {score:.4f}  {CYAN}{'█'*int(score*160)}{RESET}")
        elif hasattr(model, "coef_"):
            coef = model.coef_[0] if model.coef_.ndim > 1 else model.coef_
            fi   = pd.Series(np.abs(coef), index=X_test.columns).sort_values(ascending=False)
            mx   = fi.max() or 1
            print(f"\n  {BOLD}Top 8 Coefficients (|magnitude|):{RESET}")
            for feat, score in fi.head(8).items():
                print(f"  {str(feat):<32} {score:.4f}  {CYAN}{'█'*int(score/mx*160)}{RESET}")
 
        print(f"\n  {BOLD}Classification Report:{RESET}")
        for line in classification_report(y_te, y_pr, zero_division=0).strip().split("\n"):
            print(f"  {line}")
 
        results[name] = {
            "train_accuracy": round(train_acc, 4),
            "accuracy":    round(acc, 4),
            "f1_weighted": round(f1, 4),
            "precision":   round(prec, 4),
            "recall":      round(rec, 4),
            "roc_auc":     round(roc_auc_val, 4) if roc_auc_val is not None else None,
            "cv_mean":     res["cv_mean"],
            "cv_std":      res["cv_std"],
            "train_time":  res["training_time_sec"],
            "train_test_gap": round(train_test_gap, 4),
            "test_cv_gap": round(test_cv_gap, 4),
        }
 
    return results
 
 
def print_leaderboard(eval_results: dict):
    banner("LEADERBOARD — Model Comparison", GREEN)
 
    ranked = sorted(
        eval_results.items(),
        key=lambda x: (x[1].get("roc_auc") or x[1].get("f1_weighted") or 0),
        reverse=True,
    )
 
    hdr = (f"  {'Rank':<5} {'Model':<22} {'Accuracy':<11}"
           f"{'F1':>8} {'ROC-AUC':>10} {'CV Mean':>10} {'Time':>8}")
    print(f"\n{BOLD}{hdr}{RESET}")
    print(f"  {'─'*74}")
 
    medals = ["🥇", "🥈", "🥉"]
    for rank, (name, m) in enumerate(ranked, 1):
        medal = medals[rank-1] if rank <= 3 else "   "
        roc   = f"{m['roc_auc']:.4f}" if m.get("roc_auc") is not None else "   N/A  "
        col   = GREEN if rank == 1 else RESET
        print(f"{col}  {medal:<5} {name:<22} {m['accuracy']:<11.4f}"
              f"{m['f1_weighted']:>8.4f} {roc:>10}"
              f" {m['cv_mean']:>10.4f} {m['train_time']:>7.1f}s{RESET}")
 
    ok(f"\nBest model: {BOLD}{ranked[0][0]}{RESET}")
 
 
# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════
 
def parse_args():
    p = argparse.ArgumentParser(
        description="AutoML Pipeline — upload your dataset, run end-to-end ML with Groq AI audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python automl_pipeline.py
  python automl_pipeline.py --file titanic.csv --target Survived
  python automl_pipeline.py --file sales.xlsx --target churn --groq-model llama3-70b-8192
  python automl_pipeline.py --file data.csv --target label --cv 10 --n-iter 20
        """)
    p.add_argument("--file",       "-f", help="Path to dataset  (CSV / Excel / JSON)")
    p.add_argument("--target",     "-t", help="Target column name")
    p.add_argument("--groq-model", "-m", default=None,
                   help=f"Groq model. Options: {', '.join(GROQ_MODELS)}")
    p.add_argument("--cv",         type=int, default=5,  help="CV folds (default=5)")
    p.add_argument("--n-iter",     type=int, default=15, help="Hyperparameter search iterations (default=15)")
    p.add_argument("--no-smote",   action="store_true",  help="Disable SMOTE even if imbalance is flagged")
    return p.parse_args()
 
 
# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
 
def main():
    args = parse_args()
 
    banner("AutoML Pipeline — Standalone Runner", CYAN)
    print(f"  {DIM}Upload your dataset → AI audit (Groq) → preprocess → train → evaluate{RESET}")
    print(f"  {DIM}Requires: GROQ_API_KEY environment variable{RESET}\n")
 
    # Stage 1 — load
    df, target_col = load_dataset(args.file, args.target)
 
    # Stage 2 — profile
    profile = build_profile(df, target_col)
 
    # Stage 3 — AI audit
    flags = run_ai_audit(profile, groq_model=args.groq_model)
 
    # Stage 4 — user review
    confirmed = user_review_flags(flags)
    if args.no_smote:
        confirmed = [f for f in confirmed if f["issue_type"] != "class_imbalance"]
        info("--no-smote: SMOTE removed from confirmed fixes")
 
    # Stage 5 — preprocess
    df_clean, _ = apply_preprocessing(df.copy(), confirmed, target_col)
 
    # Stage 6 — features + split
    X_train, X_test, y_train, y_test, features, task_type = run_feature_engineering(
        df_clean, target_col, confirmed)
 
    # Stage 7 — train
    model_names = choose_models(task_type)
    trained     = train_models(model_names, X_train, y_train, n_iter=args.n_iter, cv=args.cv)
    if not trained:
        err("No models trained. Exiting.")
        sys.exit(1)
 
    # Stage 8 — evaluate
    eval_results = evaluate_all(trained, X_test, y_test, X_train, y_train)
 
    # Leaderboard
    print_leaderboard(eval_results)
 
    banner("Pipeline complete!", GREEN)
    print(f"  {DIM}All stages done. Ready to wire into FastAPI + React.{RESET}\n")
 
 
if __name__ == "__main__":
    main()