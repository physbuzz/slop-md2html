#lang sicp

(define (f-it n)
  (f-it-helper 2 1 0 n))

(define (f-it-helper a b c count)
  (if (= count 0)
    c
    (f-it-helper 
      (+ a (* 2 b) (* 3 c)) 
      a 
      b 
      (- count 1))))

(f-it 1)
(f-it 2)
(f-it 3)
(f-it 4)
(f-it 5)
(f-it 6)


