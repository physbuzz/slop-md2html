#lang sicp

(define my-num 0)
(define (f a) 
  (let ((prev my-num))
    (begin (set! my-num (+ my-num a)) 
      prev)))
;; Default evaluation
(+ (f 0) (f 1))

;; Forcing things to evaluate the opposite order
(set! my-num 0)
(let ((sec (f 1))
      (fir (f 0)))
  (+ fir sec))
