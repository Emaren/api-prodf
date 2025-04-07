"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8002";
console.log("🔧 API Base URL:", API);

const ProfilePage = () => {
  const router = useRouter();
  const [playerName, setPlayerName] = useState("");
  const [isVerified, setIsVerified] = useState(false);

  const fetchUser = async () => {
    const uid = localStorage.getItem("uid");
    if (!uid) return;

    try {
      const res = await fetch(`${API}/api/user/me`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid }),
      });

      if (!res.ok) return;

      const data = await res.json();
      if (data.in_game_name) {
        setPlayerName(data.in_game_name);
        localStorage.setItem("playerName", data.in_game_name);
      }

      setIsVerified(data.verified);
    } catch (err) {
      console.error("❌ Failed to fetch user:", err);
    }
  };

  useEffect(() => {
    let uid = localStorage.getItem("uid");

    const registerAndFetch = async () => {
      if (!uid) {
        uid = `uid-${crypto.randomUUID()}`;
        localStorage.setItem("uid", uid);

        try {
          await fetch(`${API}/api/register_user`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ uid, email: "", in_game_name: "" }),
          });
          console.log("🆕 User registered:", uid);
        } catch (err) {
          console.error("❌ Failed to register user:", err);
        }
      }

      await fetchUser();
    };

    registerAndFetch();

    // ✅ Auto-refresh verified badge on tab focus
    const handleFocus = () => {
      console.log("🔄 Refetching verification on window focus");
      fetchUser();
    };
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPlayerName(e.target.value);
  };

  const handleSaveName = async () => {
    const trimmed = playerName.trim();
    if (!trimmed) return alert("Enter a valid name.");

    localStorage.setItem("playerName", trimmed);
    const uid = localStorage.getItem("uid");
    if (!uid) return alert("UID missing");

    try {
      const res = await fetch(`${API}/api/user/update_name`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid, in_game_name: trimmed }),
      });

      if (!res.ok) throw new Error(`Status ${res.status}`);

      const result = await res.json();
      alert(`Saved! Verified: ${result.verified}`);
      setIsVerified(result.verified);
    } catch (err) {
      console.error("❌ Failed to update name:", err);
      alert("Name update likely succeeded, but verifying status failed. Please refresh.");
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Profile</h1>
      <p className="mb-4">Manage your account details and preferences here.</p>

      <div className="mb-6">
        <label htmlFor="playerName" className="block text-lg mb-2">
          Player Name{" "}
          {isVerified && <span className="text-green-400">✅ Verified</span>}
        </label>
        <Input
          id="playerName"
          value={playerName}
          onChange={handleNameChange}
          className="w-full px-4 py-3 text-lg rounded-md text-black"
          placeholder="Enter your in-game name"
        />
      </div>

      <Button
        className="mt-6 bg-blue-600 hover:bg-blue-700 px-6 py-3"
        onClick={handleSaveName}
      >
        Save Name
      </Button>

      <Button
        className="mt-6 bg-gray-600 hover:bg-gray-700 px-6 py-3"
        onClick={() => router.push("/")}
      >
        ⬅️ Back to Home
      </Button>
    </div>
  );
};

export default ProfilePage;
