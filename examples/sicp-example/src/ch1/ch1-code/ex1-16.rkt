#lang sicp

(define (powfast b n)
  (powfast-iter 1 b n))
(define (powfast-iter a b n)
  (cond ((= n 0) a)
        ((= (remainder n 2) 0) (powfast-iter a (* b b) (/ n 2)))
        (else (powfast-iter (* a b) b (- n 1)))))

(powfast 3 1)
(powfast 3 2)
(powfast 3 3)
(powfast 3 4)
(powfast 3 5)
(powfast 3 6)
(powfast 3 7)
(powfast 3 8)
