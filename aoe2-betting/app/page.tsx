"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { UserCircle, UploadCloud, Wallet } from "lucide-react";
import { useRouter } from "next/navigation";

type Bet = {
  challenger: string;
  betAmount: number;
  inactive?: boolean;
};

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8002";
console.log("🔧 API Base URL:", API);

export default function MainPage() {
  const router = useRouter();
  const [betPending, setBetPending] = useState(false);
  const [betAmount, setBetAmount] = useState(0);
  const [challenger, setChallenger] = useState("");
  const [opponent, setOpponent] = useState("");
  const [playerName, setPlayerName] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [pendingBets, setPendingBets] = useState<Bet[]>([]);
  const [betStatus, setBetStatus] = useState("");
  const [showButtons, setShowButtons] = useState(true);
  const [showNamePrompt, setShowNamePrompt] = useState(false);

  useEffect(() => {
    let uid = localStorage.getItem("uid");
    if (!uid) {
      uid = `uid-${crypto.randomUUID()}`;
      localStorage.setItem("uid", uid);
      fetch(`${API}/api/register_user`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid, email: "", in_game_name: "" }),
      }).then(() => console.log("🆕 User registered:", uid));
    }

    const storedName = localStorage.getItem("playerName");
    if (!storedName) {
      setShowNamePrompt(true);
    } else {
      setPlayerName(storedName);
    }

    const storedBets = JSON.parse(localStorage.getItem("pendingBets") || "[]");
    setPendingBets(storedBets);

    setTimeout(() => {
      setBetPending(true);
      setBetAmount(3);
      setChallenger("RedLineKey");
    }, 3000);
  }, []);

  const handleDecline = () => {
    const newBet = { challenger, betAmount, inactive: false };
    const storedBets = JSON.parse(localStorage.getItem("pendingBets") || "[]");

    const betExists = storedBets.some(
      (bet: { challenger: string; betAmount: number }) =>
        bet.challenger === challenger && bet.betAmount === betAmount
    );

    if (!betExists) {
      const updatedBets = [...storedBets, newBet];
      localStorage.setItem("pendingBets", JSON.stringify(updatedBets));
      setPendingBets(updatedBets);
    }

    setShowButtons(false);
    setTimeout(() => {
      setBetPending(false);
      setChallenger("");
      setBetAmount(0);
      setShowButtons(true);
    }, 2000);
  };

  const handleAccept = () => {
    setBetStatus("Accepted!");
    setShowButtons(false);

    setTimeout(() => {
      setBetStatus("Waiting For Battle To Start");
    }, 5000);

    setTimeout(() => {
      setBetStatus("Battle Underway!");
    }, 10000);

    setTimeout(() => {
      setBetStatus("Battle Finished! Processing Win.");
    }, 20000);
  };

  const savePlayerName = async () => {
    const trimmed = playerName.trim();
    if (!trimmed) return alert("Enter a valid name");

    localStorage.setItem("playerName", trimmed);
    setShowNamePrompt(false);

    const uid = localStorage.getItem("uid");
    if (!uid) return alert("Missing UID");

    try {
      const res = await fetch(`${API}/api/user/update_name`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid, in_game_name: trimmed }),
      });

      if (!res.ok) {
        console.warn("⚠️ Failed to sync name to backend");
      } else {
        console.log("✅ Player name synced to backend:", trimmed);
      }
    } catch (err) {
      console.error("❌ Error syncing name to backend:", err);
    }
  };

  if (showNamePrompt) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 text-white p-6">
        <Card className="bg-gray-800 shadow-xl w-full max-w-md">
          <CardContent className="p-8 flex flex-col space-y-6">
            <h1 className="text-xl font-bold text-center">Welcome to AoE2HD Betting App</h1>
            <p className="text-gray-300 text-center">
              Enter your in-game name to start betting:
            </p>
            <Input
              className="text-black px-4 py-3 text-lg rounded-md"
              placeholder="Your Steam/In-Game Name"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
            />
            <Button onClick={savePlayerName} className="w-full bg-blue-600 hover:bg-blue-700 py-3">
              Continue
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="relative w-full min-h-screen flex flex-col bg-gray-900 text-white">
      {/* My Account Menu */}
      <div className="absolute top-4 right-4 z-50">
        <button
          className="bg-gray-700 hover:bg-gray-600 flex items-center gap-2 px-5 py-3 text-lg rounded-lg shadow-md"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <UserCircle className="w-6 h-6" />
          My Accountt
        </button>
        {menuOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg overflow-hidden">
            <button className="w-full text-left px-4 py-2 hover:bg-gray-700" onClick={() => router.push("/profile")}>
              👤 Profile
            </button>
            <button className="w-full text-left px-4 py-2 hover:bg-gray-700" onClick={() => router.push("/admin/user-list")}>
              🛡️ Admin: User List
            </button>
            <button className="w-full text-left px-4 py-2 hover:bg-gray-700" onClick={() => router.push("/users")}>
              👥 Online Users
            </button>
            <button className="w-full text-left px-4 py-2 hover:bg-gray-700" onClick={() => router.push("/replay-parser")}>
              🧪 Parse Replay (Manual)
            </button>
            <button className="w-full text-left px-4 py-2 hover:bg-gray-700" onClick={() => router.push("/pending-bets")}>
              📌 Pending Bets ({pendingBets.length})
            </button>
            <button className="w-full text-left px-4 py-2 hover:bg-gray-700" onClick={() => router.push("/upload")}>
              📤 Upload Replay
            </button>
            <button className="w-full text-left px-4 py-2 hover:bg-gray-700" onClick={() => router.push("/game-stats")}>
              📊 Game Stats
            </button>
            <button className="w-full text-left px-4 py-2 hover:bg-gray-700" onClick={() => router.push("/past-earnings")}>
              💰 Past Earnings
            </button>
            <button className="w-full text-left px-4 py-2 hover:bg-gray-700" onClick={() => router.push("/settings")}>
              ⚙️ Settings
            </button>
          </div>
        )}
      </div>

      {/* Wallet */}
      <button className="fixed bottom-6 right-6 bg-gray-700 hover:bg-gray-600 p-4 rounded-full shadow-md">
        <Wallet className="w-7 h-7" />
      </button>

      {/* Main Content */}
      <div className="flex flex-col flex-1 items-center justify-center px-6 w-full max-w-2xl mx-auto space-y-14">
        <motion.div
          animate={{
            opacity: betPending ? 1 : 0.8,
            scale: betPending ? 1.1 : 1,
            boxShadow: betPending ? "0px 0px 50px rgba(59,130,246,0.9)" : "none",
          }}
          transition={{ duration: 0.5, repeat: betPending ? Infinity : 0, repeatType: "reverse" }}
          className="relative flex items-center justify-center w-64 h-64 md:w-72 md:h-72 bg-blue-700 rounded-full shadow-2xl text-5xl md:text-6xl font-bold"
        >
          AoE2
          {betPending && (
            <div className="absolute bottom-5 bg-red-500 text-white text-lg px-6 py-3 rounded-full shadow-md">
              ${betAmount} Bet Pending
            </div>
          )}
        </motion.div>

        {/* Bet Interface */}
        <Card className="w-full max-w-lg bg-gray-800 text-white shadow-xl rounded-lg">
          <CardContent className="p-8 flex flex-col items-center space-y-6">
            {betPending ? (
              <div className="text-2xl font-semibold text-center">
                <span className="text-blue-400">{challenger}</span> has challenged you!
              </div>
            ) : (
              <>
                <p className="text-gray-400 text-lg">Enter Opponent's Name:</p>
                <Input
                  className="text-black w-full px-4 py-3 text-lg rounded-md"
                  placeholder="Opponent's Steam Name"
                  value={opponent}
                  onChange={(e) => setOpponent(e.target.value)}
                />
                <Button className="mt-4 w-full text-lg bg-blue-600 hover:bg-blue-700 py-3">
                  Challenge
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        {/* Bet Status */}
        {betStatus && (
          <motion.div
            className="text-2xl font-bold text-center bg-gray-800 px-6 py-3 rounded-lg shadow-md"
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse" }}
          >
            {betStatus}
          </motion.div>
        )}

        <AnimatePresence>
          {betPending && showButtons && (
            <motion.div
              className="w-full flex gap-4 px-6 mt-6"
              initial={{ opacity: 1 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 2 }}
            >
              <Button className="bg-green-600 hover:bg-green-700 px-6 py-3 flex-grow w-2/3" onClick={handleAccept}>
                Accept
              </Button>
              <Button className="bg-red-600 hover:bg-red-700 px-6 py-3 flex-grow w-2/3" onClick={handleDecline}>
                Decline
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
