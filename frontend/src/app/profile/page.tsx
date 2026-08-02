"use client";
import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import * as api from "@/lib/api";
import type { Destination } from "@/lib/types";

function ProfileContent() {
 const { user, token, updateUser } = useAuth(); const [name, setName] = useState(user?.name || ""); const [bio, setBio] = useState(user?.bio || ""); const [avatar, setAvatar] = useState(user?.avatar_url || ""); const [saved, setSaved] = useState<Destination[]>([]); const [message, setMessage] = useState("");
 useEffect(() => { if (token) api.getFavorites(token).then(setSaved).catch(() => setSaved([])); }, [token]);
 async function save(e: React.FormEvent) { e.preventDefault(); if (!user || !token || !name.trim()) return; const updated = await api.updateProfile({ name: name.trim(), bio, avatar_url: avatar || null, preferred_tags: user.preferred_tags }, token); updateUser(updated); setMessage("Profile saved."); }
 return <div className="min-h-screen bg-ivory"><Navbar /><main className="mx-auto max-w-5xl px-4 py-10"><h1 className="font-display text-4xl text-canopy">My profile</h1><div className="mt-7 grid gap-8 md:grid-cols-2"><form onSubmit={save} className="rounded-card bg-white p-6 shadow-card"><div className="flex items-center gap-4">{avatar ? <img src={avatar} alt="Avatar preview" className="h-16 w-16 rounded-full object-cover" /> : <div className="grid h-16 w-16 place-items-center rounded-full bg-canopy text-2xl text-white">{name[0]?.toUpperCase()}</div>}<div><label className="text-sm font-semibold">Avatar image URL</label><input value={avatar} onChange={(e) => setAvatar(e.target.value)} className="mt-1 w-full rounded border p-2" placeholder="https://…" /></div></div><label className="mt-5 block text-sm font-semibold">Full name</label><input required value={name} onChange={(e) => setName(e.target.value)} className="mt-1 w-full rounded border p-2" /><label className="mt-5 block text-sm font-semibold">Bio</label><textarea value={bio} onChange={(e) => setBio(e.target.value)} maxLength={500} className="mt-1 w-full rounded border p-2" rows={4} /><button className="mt-5 rounded-full bg-laterite px-5 py-2.5 font-semibold text-white">Save profile</button>{message && <p className="mt-3 text-sm text-canopy">{message}</p>}</form><section><h2 className="font-display text-2xl text-canopy">My saved destinations</h2><div className="mt-4 space-y-3">{saved.length ? saved.map((d) => <a href={`/destinations/${d.id}`} key={d.id} className="block rounded-card bg-white p-4 shadow-card"><b>{d.name}</b><span className="ml-2 text-sm text-ink/55">{d.neighborhood}</span></a>) : <p className="text-ink/60">No saved destinations yet.</p>}</div></section></div></main></div>;
}
export default function ProfilePage() { return <ProtectedRoute><ProfileContent /></ProtectedRoute>; }
