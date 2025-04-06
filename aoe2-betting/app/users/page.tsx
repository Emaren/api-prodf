"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

type User = {
  uid: string;
  in_game_name: string;
  verified: boolean;
};

export default function OnlineUsersPage() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    fetch("/api/online_users")
      .then((res) => res.json())
      .then(setUsers);
  }, []);

  return (
    <div className="p-6 text-white">
      <h1 className="text-2xl font-bold mb-4">🟢 Online Users</h1>
      <ul className="space-y-4">
        {users.map((u) => (
          <li
            key={u.uid}
            className="bg-gray-800 p-4 rounded-lg shadow-md flex items-center justify-between"
          >
            <span>
              {u.in_game_name} {u.verified ? "✅" : "❌"}
            </span>
            <Button
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => alert(`Challenge sent to ${u.in_game_name}`)}
            >
              Challenge
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}
