import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "TwinSwing",
    short_name: "TwinSwing",
    description: "Compare your golf swing with the tour player you want to copy.",
    start_url: "/",
    display: "standalone",
    background_color: "#07140f",
    theme_color: "#07140f",
    lang: "en-GB",
  };
}
