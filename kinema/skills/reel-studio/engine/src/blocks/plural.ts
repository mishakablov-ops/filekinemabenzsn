/** Russian plural: pluralize(3, "клик|клика|кликов до записи") -> "клика до записи". Labels without "|" pass through. */
export const pluralize = (n: number, label: string) => {
  const m = label.match(/^(\S+\|\S+\|\S+)(.*)$/s);
  if (!m) return label;
  const [one, few, many] = m[1].split("|");
  const a = Math.abs(Math.round(n)) % 100;
  const b = a % 10;
  const w = a > 10 && a < 20 ? many : b === 1 ? one : b >= 2 && b <= 4 ? few : many;
  return w + m[2];
};
