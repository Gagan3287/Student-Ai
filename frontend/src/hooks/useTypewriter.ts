/**
 * useTypewriter — zero-dependency custom hook.
 *
 * Cycles through `words`, typing each in character by character,
 * pausing, then erasing before moving to the next word.
 *
 * @param words     Array of strings to cycle through
 * @param typeSpeed ms per character typed  (default 70)
 * @param eraseSpeed ms per character erased (default 40)
 * @param pauseMs   ms to pause after fully typed (default 1800)
 */
import { useEffect, useState } from "react";

export function useTypewriter(
  words: string[],
  typeSpeed = 70,
  eraseSpeed = 40,
  pauseMs = 1800
): string {
  const [displayText, setDisplayText] = useState("");
  const [wordIndex, setWordIndex] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [isErasing, setIsErasing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (words.length === 0) return;

    const currentWord = words[wordIndex % words.length];

    if (isPaused) {
      const timer = setTimeout(() => {
        setIsPaused(false);
        setIsErasing(true);
      }, pauseMs);
      return () => clearTimeout(timer);
    }

    if (!isErasing) {
      // Typing forward
      if (charIndex < currentWord.length) {
        const timer = setTimeout(() => {
          setDisplayText(currentWord.slice(0, charIndex + 1));
          setCharIndex((c) => c + 1);
        }, typeSpeed);
        return () => clearTimeout(timer);
      } else {
        // Fully typed — pause before erasing
        setIsPaused(true);
      }
    } else {
      // Erasing backward
      if (charIndex > 0) {
        const timer = setTimeout(() => {
          setDisplayText(currentWord.slice(0, charIndex - 1));
          setCharIndex((c) => c - 1);
        }, eraseSpeed);
        return () => clearTimeout(timer);
      } else {
        // Fully erased — move to next word
        setIsErasing(false);
        setWordIndex((w) => (w + 1) % words.length);
      }
    }
  }, [charIndex, isErasing, isPaused, wordIndex, words, typeSpeed, eraseSpeed, pauseMs]);

  return displayText;
}
