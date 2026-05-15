import { ImageOff } from "lucide-react";

import { useUnknownCaptureUrl } from "@/lib/hooks/useUnknowns";
import { cn } from "@/lib/utils";

type Props = {
  captureId: number | null;
  alt?: string;
  className?: string;
  /** Wrapper class — controls aspect ratio / bg. The <img> always fills it. */
  containerClassName?: string;
};

/** Renders one auth'd capture image. The endpoint requires a Bearer token,
 *  so we can't use a plain ``<img src=…>`` — the hook fetches as a Blob,
 *  exposes an object URL, and revokes it on unmount.
 */
export function UnknownFaceImage({ captureId, alt = "Unknown face", className, containerClassName }: Props) {
  const { url, loading, error } = useUnknownCaptureUrl(captureId);
  return (
    <div className={cn("relative h-full w-full overflow-hidden bg-slate-900", containerClassName)}>
      {url ? (
        <img
          src={url}
          alt={alt}
          className={cn("h-full w-full object-cover", className)}
          loading="lazy"
        />
      ) : loading ? (
        <div className="h-full w-full animate-pulse bg-slate-800" />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-slate-500" title={error ?? undefined}>
          <ImageOff className="h-8 w-8" />
        </div>
      )}
    </div>
  );
}
