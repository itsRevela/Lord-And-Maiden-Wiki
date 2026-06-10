import "./globals.css";

export const metadata = {
  title: "Lord & Maiden — Battle Simulator",
  description:
    "Find the most effective 3-hero formation. A transparent, multi-core Monte-Carlo model of the game's 8-round combat.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
