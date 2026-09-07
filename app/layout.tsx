import './globals.css';
export const metadata = {
  title: 'Prévisions ICON-EU 7 km | Alertes-météo',
  description: 'Prévisions horaires ICON-EU : température, précipitations, vent et rafales par commune en France métropolitaine.',
};
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="fr"><body>{children}</body></html>;
}
