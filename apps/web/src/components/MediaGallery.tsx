import { Image, FileText } from "lucide-react";
import type { MediaAsset } from "../lib/api";

type Props = {
  assets: MediaAsset[];
};

export function MediaGallery({ assets }: Props) {
  return (
    <section className="wide-panel media-section">
      <div className="panel-heading">
        <h2>Media</h2>
        <Image size={18} />
      </div>
      <div className="media-grid">
        {assets.slice(0, 12).map((asset) => (
          <a href={asset.url} className="media-tile" key={asset.id} target="_blank" rel="noreferrer">
            {["png", "jpg", "jpeg", "webp", "gif", "svg"].includes(asset.type) ? (
              <img src={asset.url} alt={asset.title} loading="lazy" />
            ) : (
              <div className="media-file">
                <FileText size={34} />
              </div>
            )}
            <span>{asset.title}</span>
          </a>
        ))}
      </div>
    </section>
  );
}
