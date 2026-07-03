#lang sicp

(define (sum term a next b)
  (if (> a b)
      0
      (+ (term a)
         (sum term (next a) next b))))

(define (integral f a b dx)
  (define (add-dx x) (+ x dx))
  (* (sum f (+ a (/ dx 2.0)) add-dx b) 
     dx))



(define (simp-integral f a b npts) 
  (define dx (* (- b a) (/ 2 npts)))
  (define (term-func x)
    (+ (f (- x (/ dx 2.0))) (* 4.0 (f x)) (f (+ x (/ dx 2.0)))))
  (define (add-dx x) (+ x dx))
  (* (sum term-func (+ a (/ dx 2.0)) add-dx b) 
     (/ dx 6.0) ))

(define (cube x) (* x x x))

(integral cube 0 1 0.01)
(integral cube 0 1 0.001)

(simp-integral cube 0 1 2)
(simp-integral cube 0 1 6)
(simp-integral cube 0 1 10)
(simp-integral cube 0 1 100)



