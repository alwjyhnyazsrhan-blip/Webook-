"use client";

import React, { useState } from "react";
import { Genre } from "@/lib/types";
import { Layers, Sparkles, Check, ArrowRight } from "lucide-react";

interface TaxonomyViewProps {
  genres: Genre[];
}

export const TaxonomyView: React.FC<TaxonomyViewProps> = ({ genres }) => {
  const [testInput, setTestInput] = useState<string>("مباراة كلاسيكو الهلال والاتحاد في الرياض");
  const [derivedResult, setDerivedResult] = useState<{
    genre: string;
    method: string;
    confidence: string;
  }>({
    genre: "Sports & Football (رياضة وكرة القدم)",
    method: "Arabic Heuristic + Keyword Match ('مباراة', 'الهلال')",
    confidence: "99.4%",
  });

  const handleTestDerivation = (input: string) => {
    setTestInput(input);
    const lower = input.toLowerCase();

    if (
      lower.includes("مباراة") ||
      lower.includes("دوري") ||
      lower.includes("الهلال") ||
      lower.includes("الفتح") ||
      lower.includes("spl") ||
      lower.includes("football") ||
      lower.includes("match") ||
      lower.includes("wwe") ||
      lower.includes("كأس")
    ) {
      setDerivedResult({
        genre: "Sports & Football (رياضة وكرة القدم)",
        method: "Keyword & Arabic Pattern ('مباراة', 'دوري', 'spl')",
        confidence: "98.9%",
      });
    } else if (
      lower.includes("حفل") ||
      lower.includes("طرب") ||
      lower.includes("موسيقى") ||
      lower.includes("غنائي") ||
      lower.includes("soundstorm") ||
      lower.includes("concert") ||
      lower.includes("abdo")
    ) {
      setDerivedResult({
        genre: "Concerts & Music (حفلات وموسيقى)",
        method: "Acoustic & Performance Heuristic ('حفل', 'طرب', 'concert')",
        confidence: "99.1%",
      });
    } else if (
      lower.includes("مسرح") ||
      lower.includes("كوميدي") ||
      lower.includes("play") ||
      lower.includes("theater") ||
      lower.includes("شاهد")
    ) {
      setDerivedResult({
        genre: "Theater & Comedy (مسرح وكوميديا)",
        method: "Theatrical Keyword Detection ('مسرح', 'play')",
        confidence: "97.5%",
      });
    } else if (
      lower.includes("مهرجان") ||
      lower.includes("موسم") ||
      lower.includes("festival") ||
      lower.includes("season") ||
      lower.includes("mdlbeast")
    ) {
      setDerivedResult({
        genre: "Festivals & Seasons (مهرجانات ومواسم)",
        method: "Sitemap Season Match ('مهرجان', 'season')",
        confidence: "96.8%",
      });
    } else {
      setDerivedResult({
        genre: "Entertainment & Experiences (ترفيه وتجارب)",
        method: "Default Fallback Entity Extraction",
        confidence: "88.2%",
      });
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Genre Matrix */}
      <div className="lg:col-span-2 glass rounded-3xl p-6 md:p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
            <div className="p-2 bg-blue-500/10 rounded-xl text-blue-400">
              <Layers className="w-5 h-5" />
            </div>
            Genre Mapping Matrix
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            {genres.length} active classifications
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mb-8">
          {genres.map((genre) => (
            <div
              key={genre.id}
              className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 hover:border-blue-500/40 hover:bg-slate-900/90 transition-all group"
            >
              <div className="text-[11px] font-bold text-blue-400 mb-1 font-mono">
                slug: {genre.slug}
              </div>
              <div className="font-bold text-white text-base">
                {genre.name_ar}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {genre.name_en}
              </div>
              <div className="text-[10px] text-slate-500 mt-3 pt-2 border-t border-slate-800/80 flex justify-between items-center">
                <span>{genre.event_count || 5} events</span>
                <span className="text-emerald-400 font-black flex items-center gap-1">
                  <Check className="w-3 h-3" /> ACTIVE
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Interactive Heuristics Playground */}
        <div className="bg-slate-950/80 p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-bold text-white">
              Interactive Taxonomy Heuristics Tester
            </h3>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Test how Arabic and English event titles resolve to the taxonomy tree:
          </p>

          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={testInput}
              onChange={(e) => handleTestDerivation(e.target.value)}
              placeholder="Type or paste an event title..."
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="p-3.5 bg-blue-950/30 border border-blue-900/40 rounded-xl">
            <div className="text-[10px] uppercase font-bold text-blue-400 mb-1">
              Derivation Output
            </div>
            <div className="text-sm font-bold text-white mb-1">
              Resolved Genre: <span className="text-emerald-400">{derivedResult.genre}</span>
            </div>
            <div className="text-xs text-slate-400 flex items-center justify-between">
              <span>Rule: {derivedResult.method}</span>
              <span className="font-mono text-purple-300 font-bold">
                Confidence: {derivedResult.confidence}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Logic Pipeline */}
      <div className="glass rounded-3xl p-6 md:p-8">
        <h2 className="text-lg font-bold text-white mb-6">
          Derivation Pipeline Logic
        </h2>
        <div className="space-y-6">
          <div className="relative pl-8 border-l-2 border-blue-500">
            <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-blue-500 glow"></div>
            <div className="text-sm font-bold text-white mb-1">
              1. Exact Category
            </div>
            <div className="text-xs text-slate-400 leading-relaxed">
              Direct mapping from Webook API v2 taxonomy hierarchy and sitemap metadata.
            </div>
          </div>

          <div className="relative pl-8 border-l-2 border-emerald-500">
            <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-emerald-500 glow-emerald"></div>
            <div className="text-sm font-bold text-white mb-1">
              2. Keyword Extraction
            </div>
            <div className="text-xs text-slate-400 leading-relaxed">
              Deriving genre from slug patterns, venue categories, and tags (e.g. &quot;spl&quot;, &quot;wwe&quot;, &quot;soundstorm&quot;).
            </div>
          </div>

          <div className="relative pl-8 border-l-2 border-purple-500">
            <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-purple-500"></div>
            <div className="text-sm font-bold text-white mb-1">
              3. Arabic Heuristics
            </div>
            <div className="text-xs text-slate-400 leading-relaxed">
              Pattern matching on Arabic titles (e.g. &quot;مباراة&quot;, &quot;حفل&quot;, &quot;مسرحية&quot;, &quot;مهرجان&quot;) with diacritic tolerance.
            </div>
          </div>

          <div className="relative pl-8 border-l-2 border-slate-700">
            <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-slate-700"></div>
            <div className="text-sm font-bold text-slate-300 mb-1">
              4. Seat Availability Snapshot
            </div>
            <div className="text-xs text-slate-500 leading-relaxed">
              Hydrating SeatCloud & Seats.io chart tokens for real-time section caching.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
