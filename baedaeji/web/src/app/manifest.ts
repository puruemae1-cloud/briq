import { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "배대지",
    short_name: "배대지",
    description: "영국 쇼핑몰 구매대행",
    start_url: "/",
    display: "standalone",
    background_color: "#0e1a2b",
    theme_color: "#0e1a2b",
  };
}
