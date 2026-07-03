#lang sicp

(define (make-point x y) (cons x y))
(define (x-point pt) (car pt))
(define (y-point pt) (cdr pt))
(define (print-point p)
  (newline) (display "(") (display (x-point p)) (display ",")
  (display (y-point p)) (display ")"))

;; One representation
(define (make-rect1 pos widthheight)
  (cons pos widthheight))
(define (rect-width1 rect)
  (x-point (cdr rect)))
(define (rect-height1 rect)
  (y-point (cdr rect)))
(define (rect-perimeter1 rect)
  (* 2 (+ (rect-width1 rect) (rect-height1 rect))))
(define (rect-area1 rect)
  (* (rect-width1 rect) (rect-height1 rect)))
    
;;Second representation using "top-left" and "bottom-right"
;;constraint: tl.x<br.x, tl.y<br.y
(define (make-rect2 tl br)
  (cons tl br))
(define (rect-width2 rect)
  (- (x-point (cdr rect)) (x-point (car rect))))
(define (rect-height2 rect)
  (- (y-point (cdr rect)) (y-point (car rect))))
(define (rect-perimeter2 rect)
  (* 2 (+ (rect-width2 rect) (rect-height2 rect))))
(define (rect-area2 rect)
  (* (rect-width2 rect) (rect-height2 rect)))

(display "Representation 1 (perimeter, height):")
(newline)
(let ((r1 (make-rect1 (make-point 0 0) (make-point 2 2))))
  (display (rect-perimeter1 r1)) (display ", ") 
  (display (rect-area1 r1)) (newline))

(display "Representation 2 (perimeter, height):")
(newline)
(let ((r2 (make-rect2 (make-point -1 -1) (make-point 1 1))))
  (display (rect-perimeter2 r2)) (display ", ") 
  (display (rect-area2 r2)) (newline))
