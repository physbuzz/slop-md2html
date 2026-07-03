#lang sicp

(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))
(define (accumulate-n op init seqs)
  (if (null? (car seqs))
      nil
      (cons (accumulate op init (map car seqs))
            (accumulate-n op init (map cdr seqs)))))

(define (dot-product v w)
  (accumulate + 0 (map * v w)))

(define (matrix-*-vector m v)
  (map (lambda (row) (dot-product row v)) m))

(define (transpose mat)
  (accumulate-n cons nil mat))

(define (matrix-*-matrix m n)
  (let ((cols (transpose n)))
    (map (lambda (row) (matrix-*-vector cols row)) m)))

(define (disp-vec vec) (display vec))
(define (disp-mat mat) 
  (disp-vec (car mat))
  (newline)
  (if (not (null? (cdr mat))) (disp-mat (cdr mat))))
(define mymat (list (list 1 2 3 4)
                    (list 4 5 6 6)
                    (list 6 7 8 9)))
(define mymat2 (list (list 1 0 -1 1 1)
                     (list 3 0 -1 1 -1)
                     (list 0 0 1 0 1)
                     (list 1 0 -1 0 1)))
(display "Matrix A") (newline)
(disp-mat mymat)
(display "After transpose:") (newline)
(disp-mat (transpose mymat))
(display "Matrix B") (newline)
(disp-mat mymat2)
(display "Matrix A*B:") (newline)
(disp-mat (matrix-*-matrix mymat mymat2))
