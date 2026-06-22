"use client";

export function LoadingSkeleton({
  lines = 4,
  className = "",
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="shimmer rounded-lg"
          style={{
            height: i === 0 ? "28px" : "16px",
            width: i === 0 ? "60%" : `${90 - i * 10}%`,
          }}
        />
      ))}
    </div>
  );
}

export function CardSkeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`glass-card p-5 ${className}`}>
      <div className="flex items-center gap-3 mb-4">
        <div className="shimmer rounded-xl w-10 h-10" />
        <div className="flex-1">
          <div className="shimmer rounded h-5 w-32 mb-2" />
          <div className="shimmer rounded h-3 w-20" />
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <div className="shimmer rounded h-3 w-full" />
        <div className="shimmer rounded h-3 w-4/5" />
        <div className="shimmer rounded h-3 w-3/5" />
      </div>
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="flex flex-col gap-6 p-6 animate-fade-in">
      <div className="shimmer rounded-lg h-8 w-64" />
      <div className="shimmer rounded-lg h-4 w-96" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
      <CardSkeleton />
    </div>
  );
}
