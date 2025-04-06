'use client';

import { useState } from 'react';

export default function AdminPage() {
  const [token, setToken] = useState('');
  const [users, setUsers] = useState<any[]>([]);
  const [error, setError] = useState('');

  const fetchUsers = async () => {
    setError('');
    try {
      const res = await fetch('http://localhost:8002/admin/users', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      }
      const data = await res.json();
      setUsers(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="p-8 font-sans">
      <h1 className="text-2xl font-bold mb-2">🔐 Admin Dashboard</h1>
      <p className="mb-4 text-gray-600">View all registered users</p>

      <div className="mb-6">
        <input
          type="password"
          placeholder="Enter admin token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="border p-2 rounded w-64"
        />
        <button
          onClick={fetchUsers}
          className="ml-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Fetch Users
        </button>
      </div>

      {error && <p className="text-red-600">❌ {error}</p>}

      {users.length > 0 && (
        <table className="table-auto w-full mt-4 border">
          <thead>
            <tr className="bg-gray-100">
              <th className="border px-4 py-2">UID</th>
              <th className="border px-4 py-2">Email</th>
              <th className="border px-4 py-2">In-Game Name</th>
              <th className="border px-4 py-2">Verified</th>
              <th className="border px-4 py-2">Created At</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.uid}>
                <td className="border px-4 py-2">{u.uid}</td>
                <td className="border px-4 py-2">{u.email}</td>
                <td className="border px-4 py-2">{u.in_game_name}</td>
                <td className="border px-4 py-2">{u.verified ? '✅' : '❌'}</td>
                <td className="border px-4 py-2">{u.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
