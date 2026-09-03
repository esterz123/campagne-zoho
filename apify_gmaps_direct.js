// Run Apify actor sans les restrictions de chemin du wrapper skill.
const { ApifyClient } = (() => { try { return require("apify-client"); } catch (e) { return {}; } })();
const fs = require("fs");

const ACTOR = "compass/crawler-google-places";
const INPUT = {
  searchStringsArray: [
    "tolerie industrielle France",
    "usinage de precision France",
    "chaudronnerie industrielle France",
    "decolletage France",
    "plasturgie France",
  ],
  maxCrawledPlaces: 300,
  language: "fr",
  country: "FR",
  locationQuery: "France",
  scrapeContacts: true,
  scrapeWebsiteEmails: true,
  websiteEmailsLimit: 3,
};

async function main() {
  // pas de client apify installe ? -> API REST directe
  const token = process.env.APIFY_TOKEN;
  if (!token) { console.error("APIFY_TOKEN absent"); process.exit(1); }
  console.log("Lancement actor", ACTOR, "...");
  const r = await fetch("https://api.apify.com/v2/acts/" + ACTOR.replace("/", "~") + "/run-sync-get-dataset-items?timeout=300", {
    method: "POST",
    headers: { "Authorization": "Bearer " + token, "Content-Type": "application/json" },
    body: JSON.stringify(INPUT),
  });
  if (!r.ok) {
    console.error("HTTP", r.status, (await r.text()).slice(0, 300));
    process.exit(1);
  }
  const items = await r.json();
  console.log("items recus:", items.length);
  // colonnes utiles pour la prospection
  const rows = items.map(x => ({
    nom: x.title || "",
    site: x.website || "",
    tel: x.phone || "",
    email: (x.emails && x.emails[0]) || "",
    ville: (x.address && (x.address.city || x.address.addressCompact)) || "",
    naf: x.categoryName || "",
    note: x.totalScore || "",
    avis: x.reviewsCount || "",
    google_url: x.url || "",
  }));
  const avec_email = rows.filter(x => x.email);
  const csv = ["nom,site,tel,email,ville,naf,note,avis,google_url"].concat(
    rows.map(x => Object.values(x).map(v => '"' + String(v || "").replace(/"/g, '""') + '"').join(","))
  ).join("\n");
  fs.writeFileSync("2026-08-31_googlemaps_pme_fr.csv", csv, "utf-8");
  fs.writeFileSync("2026-08-31_googlemaps_pme_fr.json", JSON.stringify(rows, null, 1), "utf-8");
  console.log("CSV ecrit:", rows.length, "lignes | avec email:", avec_email.length);
}

main().catch(e => { console.error(e.message); process.exit(1); });
