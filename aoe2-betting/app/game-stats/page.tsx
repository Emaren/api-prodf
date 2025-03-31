"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

// --- Interfaces ---
interface PlayerStats {
  name: string;
  civilization: number;
  civilization_name: string;
  winner: boolean;
  military_score: number;
  economy_score: number;
  technology_score: number;
  society_score: number;
  units_killed: number;
  buildings_destroyed: number;
  resources_gathered: number;
  fastest_castle_age: number;
  fastest_imperial_age: number;
  relics_collected: number;
}

interface GameStats {
  id: number;
  game_version: string;
  map: any;
  game_type: string;
  duration: number;
  players: PlayerStats[];
  timestamp: string;
}

function cleanGameType(rawType: string): string {
  const match = rawType.match(/'(VER.*?)'/);
  return match && match[1] ? match[1] : rawType;
}

function formatDuration(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const remainder = totalSeconds % 3600;
  const minutes = Math.floor(remainder / 60);
  const secs = remainder % 60;

  if (hours > 0 && minutes > 0 && secs > 0) {
    return `${hours} hours ${minutes} minutes ${secs} seconds`;
  } else if (hours > 0 && minutes > 0) {
    return `${hours} hours ${minutes} minutes`;
  } else if (hours > 0) {
    return `${hours} hours`;
  } else if (minutes > 0 && secs > 0) {
    return `${minutes} minutes ${secs} seconds`;
  } else if (minutes > 0) {
    return `${minutes} minutes`;
  } else {
    return `${secs} seconds`;
  }
}

function sanitizeDuration(seconds: number): number {
  // If match length is extremely large or too short, treat it as invalid
  if (seconds > 4 * 3600 || seconds < 10) {
    return 0;
  }
  return seconds;
}

const GameStatsPage = () => {
  const router = useRouter();
  const [games, setGames] = useState<GameStats[]>([]);
  const [loading, setLoading] = useState(true);

  // If you want to toggle premium fields, set this or retrieve from user status
  const isPremiumUser = false;

  useEffect(() => {
    const fetchGameStats = async () => {
      try {
        const response = await fetch(`/api/game_stats?ts=${Date.now()}`, {
          cache: "no-store",
        });
        
        const data = await response.json();
        console.log("🔍 RAW API Response:", data);

        if (!Array.isArray(data)) {
          console.warn("⚠️ No game stats array found in API response.");
          setLoading(false);
          return;
        }

        // Convert any string-ified players or map fields
        const formattedGames = data.map((game: GameStats) => {
          let safePlayers = game.players;
          if (typeof safePlayers === "string") {
            try {
              safePlayers = JSON.parse(safePlayers);
            } catch {}
          }

          let safeMap = game.map;
          if (typeof safeMap === "string") {
            try {
              safeMap = JSON.parse(safeMap);
            } catch {}
          }

          return {
            ...game,
            players: safePlayers,
            map: safeMap,
          };
        });

        // Only keep matches that have at least 1 player
        const validGames = formattedGames.filter(
          (g) => g.players && g.players.length > 0
        );
        if (validGames.length === 0) {
          console.warn("⚠️ All parsed games have empty player lists.");
          setLoading(false);
          return;
        }

        setGames(validGames);
        setLoading(false);
      } catch (err) {
        console.error("❌ Error fetching game stats:", err);
        setLoading(false);
      }
    };

    fetchGameStats();
    // Optionally poll every few seconds for updates
    const interval = setInterval(fetchGameStats, 3000);
    return () => clearInterval(interval);
  }, []);

  function showStat<T extends string | number>(
    actualValue: T,
    suffix?: string
  ): React.ReactNode {
    // Only reveal real stats if premium
    return isPremiumUser ? (
      <>
        {actualValue}
        {suffix ? ` ${suffix}` : ""}
      </>
    ) : (
      <span className="text-gray-400 italic">Premium Stats</span>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <h2 className="text-3xl font-bold text-center mb-6 text-gray-400">
        Game Stats
      </h2>

      {loading ? (
        <p className="text-center text-gray-400">Loading game stats...</p>
      ) : games.length === 0 ? (
        <p className="text-center text-gray-400">No game stats available.</p>
      ) : (
        <div className="space-y-6">
          {games.map((game, index) => {
            // index=0 => newest => "🔥 Latest Match"
            // index=1 => "Previous Match #1"
            // index=2 => "Previous Match #2"
            const isLatest = index === 0;
            const matchNumber = games.length - index;
            const cleanedDuration = sanitizeDuration(game.duration);

            return (
              <div
                key={game.id}
                className={`p-6 rounded-xl shadow-lg transition-all ${
                  isLatest
                    ? "bg-gray-900 text-yellow-400 border-2 border-yellow-500"
                    : "bg-gray-700 text-black border border-gray-600"
                }`}
              >
                <h3 className="text-2xl font-semibold">
                  {isLatest
                    ? "🔥 Latest Match"
                    : `Previous Match #${matchNumber}`
                  }
                </h3>

                <p className="text-lg">
                  <strong>Game Version:</strong>{" "}
                  {typeof game.game_version === "string" 
                  ? game.game_version.replace("Version.", "") 
                  : JSON.stringify(game.game_version)}

                </p>
                <p className="text-lg">
                  <strong>Map:</strong>{" "}
                  {typeof game.map === "object" ? game.map?.name : game.map}
                </p>
                <p className="text-lg">
                  <strong>Game Type:</strong>{" "}
                  {cleanGameType(game.game_type).replace("VER ", "v")}
                </p>
                <p className="text-lg">
                  <strong>Duration:</strong>{" "}
                  {cleanedDuration === 0
                    ? "⚠️ Invalid Duration (Likely Out of Sync)"
                    : formatDuration(cleanedDuration)}
                </p>

                <h4 className="text-xl font-semibold mt-4">Players</h4>
                <div className="mt-2 space-y-2">
                  {game.players.map((player, pIdx) => (
                    <div
                      key={pIdx}
                      className={`p-4 rounded-lg ${
                        player.winner
                          ? "bg-gray-500 text-black font-bold"
                          : "bg-gray-600 text-black"
                      }`}
                    >
                      <p>
                        <strong>Name:</strong> {player.name}{" "}
                        {player.winner ? (
                          <span className="text-yellow-300 font-bold">🏆</span>
                        ) : (
                          <span className="text-red-400 italic">❌</span>
                        )}
                      </p>
                      <p>
                        <strong>Civilization:</strong>{" "}
                        {player.civilization_name || player.civilization}
                      </p>
                      <p>
                        <strong>Military Score:</strong>{" "}
                        {showStat(player.military_score)}
                      </p>
                      <p>
                        <strong>Economy Score:</strong>{" "}
                        {showStat(player.economy_score)}
                      </p>
                      <p>
                        <strong>Technology Score:</strong>{" "}
                        {showStat(player.technology_score)}
                      </p>
                      <p>
                        <strong>Society Score:</strong>{" "}
                        {showStat(player.society_score)}
                      </p>
                      <p>
                        <strong className="italic">More</strong>{" "}
                        {showStat(player.units_killed)}
                      </p>
                    </div>
                  ))}
                </div>

                {!game.players.some((p) => p.winner) && (
                  <p className="text-red-500 italic mt-4">
                    ⚠️ No winner detected. Match likely ended in Out of Sync.
                    All bets refunded.
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="text-center mt-8">
        <Button
          className="bg-blue-700 hover:bg-blue-700 px-6 py-3 text-white font-semibold"
          onClick={() => router.push("/")}
        >
          ⬅️ Back to Home
        </Button>
      </div>
    </div>
  );
};

export default GameStatsPage;
