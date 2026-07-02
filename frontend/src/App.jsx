import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Play, Code, BarChart2, CheckCircle2, AlertTriangle, Zap } from 'lucide-react';

const DEFAULT_JAVA_CODE = `package runner;

public class UserSolution implements Sorter {
    @Override
    public void sort(int[] arr) {
        if (arr == null || arr.length == 0) return;
        
        int max = arr[0];
        for (int num : arr) {
            if (num > max) {
                max = num;
            }
        }
        
        int[] count = new int[max + 1];
        for (int num : arr) {
            count[num]++;
        }
        
        int index = 0;
        for (int i = 0; i < count.length; i++) {
            while (count[i] > 0) {
                arr[index++] = i;
                count[i]--;
            }
        }
    }
}`;

export default function App() {
  const [code, setCode] = useState(DEFAULT_JAVA_CODE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // New Configuration States
  const [dataType, setDataType] = useState('integer');
  const [arrayState, setArrayState] = useState('random');
  const [rangeStart, setRangeStart] = useState(0);
  const [rangeEnd, setRangeEnd] = useState(100);
  const [mustHave, setMustHave] = useState("");

  const [dryRunOutput, setDryRunOutput] = useState(null);

  React.useEffect(() => {
    setDryRunOutput(null);
  }, [code, dataType, arrayState, rangeStart, rangeEnd]);

  const handleDryRun = async () => {
    setLoading(true);
    setError(null);
    setDryRunOutput(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/dryrun', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            code, dataType, arrayState,
            rangeStart: parseInt(rangeStart) || 0,
            rangeEnd: parseInt(rangeEnd) || 100,
            mustHave: mustHave
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.error || "Server Error");
      }
      if (!data.success) throw new Error(data.error || "Unknown Error");
      setDryRunOutput(data.output);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/benchmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            code,
            dataType,
            arrayState,
            rangeStart: parseInt(rangeStart) || 0,
            rangeEnd: parseInt(rangeEnd) || 100,
            mustHave: mustHave
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.error || "Server Error");
      }
      if (!data.success) {
        throw new Error(data.detail || data.error || "Unknown pipeline error occurred.");
      }
      
      const chartData = data.metrics.sizes.map((size, index) => ({
        size,
        runtime: data.metrics.runtimes[index],
      }));

      setResult({
        chartData,
        complexity: data.analysis.estimated_complexity,
        confidence: data.analysis.confidence_percentage,
        errors: data.analysis.model_residual_errors,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#141414] text-slate-200 font-sans">
      <header className="flex items-center justify-between px-6 py-4 bg-[#F0B74A] border-b-4 border-yellow-600 shadow-lg">
        <div className="flex items-center space-x-3">
          <Zap className="w-7 h-7 text-[#141414]" />
          <h1 className="text-2xl font-black text-[#141414] tracking-tighter">optim <span className="text-xs bg-black text-[#F0B74A] px-2 py-0.5 rounded-sm ml-2">v2.0.0-Beta</span></h1>
        </div>
        <div className="text-xs font-mono font-semibold text-[#141414] tracking-widest bg-yellow-600/20 px-4 py-1 rounded">
          Empirical Performance Judgment Engine <span className="bg-black text-[#F0B74A] px-1 rounded ml-2">V2</span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        
        {/* LEFT CONSOLE: Code Editor */}
        <div className="w-1/2 flex flex-col border-r border-[#333]">
          
          {/* Header Bar */}
          <div className="bg-[#1A1A1A] px-4 py-3 border-b border-[#424242] flex items-center justify-between">
            <div className="flex items-center space-x-2 text-yellow-500 font-mono text-sm">
              <Code className="w-4 h-4" />
              <span>UserSolution.java</span>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleDryRun}
                disabled={loading}
                className="flex items-center space-x-2 bg-slate-700 hover:bg-slate-600 text-white px-4 py-1.5 rounded text-sm font-bold shadow transition-colors disabled:opacity-50"
              >
                {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Play className="w-4 h-4" />}
                <span>1. Dry Run (N=15)</span>
              </button>
              <button
                onClick={handleRunAnalysis}
                disabled={loading || !dryRunOutput}
                className="flex items-center space-x-2 bg-[#F0B74A] hover:bg-[#ffc85c] text-black px-4 py-1.5 rounded text-sm font-bold shadow-md transition-colors disabled:opacity-50"
              >
                {loading ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : <Play className="w-4 h-4" />}
                <span>2. Execute Analysis</span>
              </button>
            </div>
          </div>

          {/* Benchmark Configuration Toolbar */}
          <div className="bg-[#1A1A1A]/80 border-b border-[#424242] px-4 py-2.5 flex flex-wrap gap-5 text-xs font-mono text-slate-300 items-center">
             <div className="flex items-center space-x-2">
                <label className="uppercase font-bold tracking-wider text-slate-500">Type:</label>
                <select value={dataType} onChange={e => setDataType(e.target.value)} className="bg-[#242424] border border-[#424242] rounded px-2 py-1 outline-none text-[#F0B74A] cursor-pointer">
                  <option value="integer">Integer</option>
                  <option value="decimal">Decimal</option>
                </select>
             </div>
             <div className="flex items-center space-x-2">
                <label className="uppercase font-bold tracking-wider text-slate-500">State:</label>
                <select value={arrayState} onChange={e => setArrayState(e.target.value)} className="bg-[#242424] border border-[#424242] rounded px-2 py-1 outline-none text-[#F0B74A] cursor-pointer">
                  <option value="random">Randomised</option>
                  <option value="sorted">Sorted</option>
                  <option value="nearly_sorted">Nearly Sorted (10% swapped)</option>
                </select>
             </div>
             <div className="flex items-center space-x-2">
                <label className="uppercase font-bold tracking-wider text-slate-500">Range:</label>
                <input type="number" value={rangeStart} onChange={e => setRangeStart(e.target.value)} className="w-16 bg-[#242424] border border-[#424242] rounded px-2 py-1 outline-none text-[#F0B74A]" />
                <span className="text-slate-500">to</span>
                <input type="number" value={rangeEnd} onChange={e => setRangeEnd(e.target.value)} className="w-20 bg-[#242424] border border-[#424242] rounded px-2 py-1 outline-none text-[#F0B74A]" />
             </div>
             <div className="flex items-center space-x-2">
                <label className="uppercase font-bold tracking-wider text-slate-500" title="Comma-separated values to forcefully inject">Must Have:</label>
                <input type="text" placeholder="e.g. 42, -5" value={mustHave} onChange={e => setMustHave(e.target.value)} className="w-32 bg-[#242424] border border-[#424242] rounded px-2 py-1 outline-none text-[#F0B74A] text-xs placeholder-[#424242]" />
             </div>
          </div>

          {/* Polynomial Safety Warning */}
          <div className="bg-yellow-950/40 border-b border-yellow-900/50 px-4 py-2 flex items-center space-x-2 text-xs font-mono text-yellow-500">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>⚠ This analyzer only supports polynomial-time algorithms up to O(N³).</span>
            <div className="relative group flex items-center">
              <div className="w-4 h-4 rounded-full border border-yellow-500 flex items-center justify-center cursor-help text-[10px] font-bold">i</div>
              <div className="absolute left-6 top-1/2 -translate-y-1/2 hidden group-hover:flex bg-[#1A1A1A] border border-[#424242] p-2 rounded shadow-xl text-slate-300 w-64 z-50 flex-col space-y-1">
                <span className="font-bold text-[#F0B74A] border-b border-[#333] pb-1 mb-1">Supported Complexities:</span>
                <span>• O(1) Constant</span>
                <span>• O(log N) Logarithmic</span>
                <span>• O(N^(1/3)) Cube Root</span>
                <span>• O(sqrt(N)) Square Root</span>
                <span>• O(N) Linear</span>
                <span>• O(N log N) Linearithmic</span>
                <span>• O(N²) Quadratic</span>
                <span>• O(N³) Cubic</span>
              </div>
            </div>
          </div>

          <div className="flex-1 min-h-[550px] bg-[#1A1A1A] text-left flex flex-col">
            <Editor
              height={dryRunOutput ? "60%" : "100%"}
              defaultLanguage="java"
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value || '')}
              options={{
                fontSize: 14,
                minimap: { enabled: false },
                lineHeight: 22,
                fontFamily: 'Fira Code, Consolas, Monaco, monospace',
                tabSize: 4,
              }}
            />
            {dryRunOutput && (
              <div className="h-[40%] border-t-2 border-[#424242] bg-black text-[#10B981] font-mono text-sm p-4 overflow-y-auto shadow-inner whitespace-pre-wrap">
                <div className="flex items-center space-x-2 text-slate-400 mb-2 font-bold uppercase text-xs tracking-widest border-b border-[#333] pb-2">
                  <Play className="w-3 h-3" />
                  <span>Dry Run Output</span>
                </div>
                {dryRunOutput}
              </div>
            )}
          </div>
        </div>

        {/* Right Console: Metric Visualization Graphs & Mathematical Analysis */}
        <div className="flex flex-col space-y-6 h-full justify-start">

          {/* Welcome/Empty State */}
          {!result && !error && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-[#BF9300]/30 rounded-xl p-8 text-center text-slate-500 bg-[#242424]/40 min-h-[400px]">
              <BarChart2 className="h-12 w-12 mb-4 text-[#424242]" />
              <p className="text-base font-semibold text-[#F0B74A]">Ready for Execution Profiling</p>
              <p className="text-sm max-w-sm mt-1 text-slate-400">Paste your implementation logic and run the analysis to compute empirical coordinate tracking vectors.</p>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center bg-[#242424] border border-[#424242] rounded-xl p-8 min-h-[400px]">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#F0B74A] mb-4"></div>
              <p className="text-sm font-mono text-[#F0B74A]">Generating deterministic arrays...</p>
              <p className="text-xs text-slate-400 mt-1">Running dynamic iteration scaling out-of-band</p>
            </div>
          )}

          {/* Error Alert Display */}
          {error && (
            <div className="bg-red-950/20 border border-red-900 rounded-xl p-4 flex items-start space-x-3 text-red-200">
              <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="w-full">
                <h4 className="font-bold text-sm text-red-400 uppercase tracking-wider">Pipeline Execution Exception</h4>
                <pre className="text-xs mt-2 bg-[#1A1A1A] p-3 rounded font-mono overflow-x-auto text-red-400 border border-[#424242] text-left w-full">
                  {error}
                </pre>
              </div>
            </div>
          )}

          {/* Metrics Results Cards */}
          {result && (
            <>
              {/* Core Math Metric Header Cards */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-[#242424] to-[#1A1A1A] border border-[#424242] rounded-xl p-5 relative overflow-hidden text-left">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Estimated Complexity</span>
                  <span className="text-3xl font-black font-mono text-red-400 mt-2 block tracking-tight">
                    {result.complexity}
                  </span>
                  <div className="absolute right-4 bottom-2 text-[#424242]/30 font-mono text-7xl font-bold select-none z-0 pointer-events-none">O</div>
                </div>

                <div className="bg-gradient-to-br from-[#242424] to-[#1A1A1A] border border-[#BF9300]/20 rounded-xl p-5 text-left">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Model Fit Confidence</span>
                  <span className="text-3xl font-black font-mono text-[#06B6D4] mt-2 block">
                    {result.confidence}%
                  </span>
                  <div className="flex items-center space-x-1.5 mt-2 text-xs text-[#06B6D4] font-mono">
                    <CheckCircle2 className="h-3.5 w-3.5 text-[#06B6D4]" />
                    <span className="text-slate-300">Validated via non-linear least squares</span>
                  </div>
                </div>
              </div>

              {/* JIT Microsecond Warning Notice Block */}
              <div className="bg-[#242424] border border-[#424242] rounded-xl px-4 py-3 text-xs text-slate-400 font-mono">
                <span className="text-[#F0B74A] font-bold">Profiling Note:</span> Multi-run aggregation loop active. Microsecond metrics normalized via dynamic JIT scaling per array size.
              </div>

              {/* The Recharts Empirical Graph Component */}
              <div className="bg-[#242424] border border-[#424242] rounded-xl p-5 flex flex-col h-[450px] text-left">
                <h3 className="text-sm font-bold text-[#F0B74A] mb-4 flex items-center space-x-2">
                  <BarChart2 className="h-4 w-4 text-[#F0B74A]" />
                  <span>Empirical Performance Curve (T vs N)</span>
                </h3>
                <div className="flex-1 min-h-0 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={result.chartData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#424242" />
                      <XAxis dataKey="size" stroke="#64748b" tick={{ fontSize: 11 }} label={{ value: 'Array Size (N)', position: 'insideBottomRight', offset: -10, fill: '#64748b', fontSize: 11 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 11 }} label={{ value: 'Runtime (ms)', angle: -90, position: 'insideLeft', offset: 0, fill: '#64748b', fontSize: 11 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#1A1A1A', borderColor: '#334155', color: '#f1f5f9', fontFamily: 'monospace' }} />
                      <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                      <Line name="Measured JIT Runtime" type="monotone" dataKey="runtime" stroke="#06B6D4" strokeWidth={3} dot={{ fill: '#06B6D4', r: 4 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}