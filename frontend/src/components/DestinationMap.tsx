"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useEffect, useRef, useState } from "react";
import Button from "@/components/Button";

declare global { interface Window { google?: any; } }

function loadMaps(key: string): Promise<any> {
  if (window.google?.maps) return Promise.resolve(window.google.maps);
  return new Promise((resolve, reject) => {
    const existing = document.getElementById("google-maps-js");
    if (existing) { existing.addEventListener("load", () => resolve(window.google?.maps), { once: true }); existing.addEventListener("error", () => reject(), { once: true }); return; }
    const script = document.createElement("script"); script.id = "google-maps-js"; script.async = true;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}`;
    script.onload = () => resolve(window.google?.maps); script.onerror = reject; document.head.appendChild(script);
  });
}

export default function DestinationMap({ name, latitude, longitude }: { name: string; latitude: number; longitude: number }) {
  const node = useRef<HTMLDivElement>(null); const map = useRef<any>(null); const renderer = useRef<any>(null);
  const [message, setMessage] = useState(""); const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
  useEffect(() => {
    if (!key || !node.current) return; let cancelled = false;
    loadMaps(key).then((maps) => { if (cancelled || !maps) return; const position = { lat: latitude, lng: longitude }; map.current = new maps.Map(node.current, { center: position, zoom: 15, mapTypeControl: false, streetViewControl: false }); new maps.Marker({ map: map.current, position, title: name }); renderer.current = new maps.DirectionsRenderer({ map: map.current, polylineOptions: { strokeColor: "#2563eb", strokeWeight: 5 } }); }).catch(() => setMessage("Google Maps could not load. Check the API key and Maps JavaScript API."));
    return () => { cancelled = true; };
  }, [key, latitude, longitude, name]);
  function route() {
    if (!navigator.geolocation) { setMessage("Your browser does not support location services."); return; }
    setMessage("Finding your location…"); navigator.geolocation.getCurrentPosition((position) => {
      if (!window.google?.maps || !renderer.current) return;
      new window.google.maps.DirectionsService().route({ origin: { lat: position.coords.latitude, lng: position.coords.longitude }, destination: { lat: latitude, lng: longitude }, travelMode: window.google.maps.TravelMode.DRIVING }, (result: any, status: string) => { if (status === "OK") { renderer.current.setDirections(result); setMessage("Route shown in blue."); } else setMessage("A driving route could not be calculated."); });
    }, () => setMessage("Location permission is needed to show a route."));
  }
  if (!key) return <p className="rounded-card bg-marigold/15 text-ink/70 p-4 text-sm">Add <code>NEXT_PUBLIC_GOOGLE_MAPS_API_KEY</code> to enable the interactive map.</p>;
  return <section className="mt-10"><h2 className="font-display text-2xl text-canopy mb-4">Explore on the map</h2><div ref={node} className="h-80 w-full rounded-card overflow-hidden bg-canopy/10" aria-label={`Map of ${name}`} />{message && <p className="mt-3 text-sm text-ink/65">{message}</p>}<div className="flex flex-wrap gap-3 mt-4"><Button onClick={route}>Show Route from My Location</Button><a href={`https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`} target="_blank" rel="noreferrer" className="inline-flex items-center justify-center rounded-full px-5 py-2.5 text-sm font-semibold text-canopy border border-canopy/25 hover:bg-canopy/5">🚗 Open Turn-by-Turn in Google Maps</a></div></section>;
}
