"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";


export default function ReplayParserPage() {
  const [status, setStatus] = useState("");
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleSelectReplay = async () => {
    try {
      if ("showDirectoryPicker" in window) {
        setStatus("Opening folder picker...");
        const dirHandle = await (window as any).showDirectoryPicker();
        let latestFile: File | null = null;
        let latestModified = 0;

        for await (const [name, handle] of dirHandle.entries()) {
          if (name.endsWith(".aoe2record") && handle.kind === "file") {
            const file = await handle.getFile();
            if (file.lastModified > latestModified) {
              latestModified = file.lastModified;
              latestFile = file;
            }
          }
        }

        if (!latestFile) {
          setStatus("No .aoe2record files found.");
          return;
        }

        await uploadReplayFile(latestFile);
      } else {
        // Fallback to <input type="file">
        fileInputRef.current?.click();
      }
    } catch (err) {
      console.error(err);
      setStatus("Error selecting file or folder.");
    }
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await uploadReplayFile(file);
  };

  const uploadReplayFile = async (file: File) => {
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8002";
    setFileName(file.name);
    setStatus(`Uploading ${file.name}...`);
  
    const formData = new FormData();
    formData.append("file", file);
  
    try {
      const res = await fetch(`${API_BASE}/api/parse_replay`, {
        method: "POST",
        body: formData,
      });
  
      if (res.ok) {
        setStatus(`✅ Parsed: ${file.name}`);
      } else {
        const msg = await res.text();
        setStatus(`❌ Error: ${msg}`);
      }
    } catch (err) {
      console.error(err);
      setStatus("❌ Upload failed.");
    }
  };
  

  return (
    <div className="p-6 space-y-4 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold">Manual Replay Parser</h1>
      <p>
        Select your SaveGame folder (Chrome/Edge) or upload a <code>.aoe2record</code> file
        manually (Safari/Firefox).
      </p>

      <button
        onClick={handleSelectReplay}
        className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
      >
        Select Replay Folder or File
      </button>

      <input
        type="file"
        accept=".aoe2record,application/octet-stream,*/*"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
      <br></br>
      <br></br>
      <br></br>
      <a
        href="https://drive.google.com/uc?export=download&id=1mDb4CxcyH_9X6ERLTfKbqrD5dEN6vg8n"
        target="_blank"
        rel="noopener noreferrer"
        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg inline-block"
      >
        ⬇️ Download AoE2 Watcher for macOS (.dmg)
      </a>
      <br />
      <br />
      <br />
      <Button
          className="mt-4 text-lg text-gray-400 hover:text-white"
          onClick={() => router.push("/")}
        >
          ← Back to Home
      </Button>
      {fileName && <p className="text-sm text-gray-600">Selected: {fileName}</p>}
      {status && <p className="text-sm mt-2">{status}</p>}
    </div>
  );
}
