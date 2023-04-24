open Ast

type expr_p =
  {
    neg_p : float;
    plus_p : float;
    minus_p : float;
    times_p : float;
    div_p : float;
    mod_p : float;
    less_than_p : float;
    less_equal_p : float;
    greater_than_p : float;
    greater_equal_p : float;
    equal_p : float;
    not_equal_p : float;

    logical_and_p : float;
    logical_or_p : float;
    not_p : float;

    bitwise_and_p : float;
    bitwise_or_p : float;
    bitwise_complement_p : float;
    bitwise_xor_p : float;
    left_shift_p : float;
    right_shift_p : float;

    x_p : float;
    y_p : float;
    int_lit_p : float;
  }

let max_depth = 3

let choose state l p =
  let roll = Random.State.float state 1.0 in
  let rec choose' l p acc =
    match l, p with
    | [], [] -> failwith "choose: empty list"
    | [], _ -> failwith "choose: list and probability list have different lengths"
    | _, [] -> failwith "choose: list and probability list have different lengths"
    | x :: xs, y :: ys ->
      if roll < acc +. y then
        x
      else
        choose' xs ys (acc +. y) in
  choose' l p 0.0

let random_int_lit state =
  let n = Random.State.bits state in
  IntLit n

let random_terminal state p = 
  let normalized_p = List.map (fun x -> x /. (List.fold_left (+.) 0.0 p)) p in
  choose state [lazy X; lazy Y; lazy (random_int_lit state)] normalized_p

let rec random_expr seed state depth p =
  choose state [
      lazy (Neg (random_ast (seed + 1) (depth + 1) p));
      lazy (Plus (random_ast (seed + 2) (depth + 1) p, random_ast (seed + 3) (depth + 1) p));
      lazy (Minus (random_ast (seed + 4) (depth + 1) p, random_ast (seed + 5) (depth + 1) p));
      lazy (Times (random_ast (seed + 6) (depth + 1) p, random_ast (seed + 7) (depth + 1) p));
      lazy (Div (random_ast (seed + 8) (depth + 1) p, random_ast (seed + 9) (depth + 1) p));
      lazy (Mod (random_ast (seed + 10) (depth + 1) p, random_ast (seed + 11) (depth + 1) p));
      lazy (LessThan (random_ast (seed + 12) (depth + 1) p, random_ast (seed + 13) (depth + 1) p));
      lazy (LessEqual (random_ast (seed + 14) (depth + 1) p, random_ast (seed + 15) (depth + 1) p));
      lazy (GreaterThan (random_ast (seed + 16) (depth + 1) p, random_ast (seed + 17) (depth + 1) p));
      lazy (GreaterEqual (random_ast (seed + 18) (depth + 1) p, random_ast (seed + 19) (depth + 1) p));
      lazy (Equal (random_ast (seed + 20) (depth + 1) p, random_ast (seed + 21) (depth + 1) p));
      lazy (NotEqual (random_ast (seed + 22) (depth + 1) p, random_ast (seed + 23) (depth + 1) p));

      lazy (LogicalAnd (random_ast (seed + 24) (depth + 1) p, random_ast (seed + 25) (depth + 1) p));
      lazy (LogicalOr (random_ast (seed + 26) (depth + 1) p, random_ast (seed + 27) (depth + 1) p));
      lazy (Not (random_ast (seed + 28) (depth + 1) p));

      lazy (BitwiseAnd (random_ast (seed + 29) (depth + 1) p, random_ast (seed + 30) (depth + 1) p));
      lazy (BitwiseOr (random_ast (seed + 31) (depth + 1) p, random_ast (seed + 32) (depth + 1) p));
      lazy (BitwiseComplement (random_ast (seed + 33) (depth + 1) p));
      lazy (BitwiseXor (random_ast (seed + 34) (depth + 1) p, random_ast (seed + 35) (depth + 1) p));
      lazy (LeftShift (random_ast (seed + 36) (depth + 1) p, random_ast (seed + 37) (depth + 1) p));
      lazy (RightShift (random_ast (seed + 38) (depth + 1) p, random_ast (seed + 39) (depth + 1) p));

      lazy X;
      lazy Y;
      lazy (random_int_lit state)
    ] [ 
      p.neg_p; 
      p.plus_p;
      p.minus_p;
      p.times_p;
      p.div_p;
      p.mod_p;
      p.less_than_p;
      p.less_equal_p;
      p.greater_than_p;
      p.greater_equal_p;
      p.equal_p;
      p.not_equal_p;

      p.logical_and_p;
      p.logical_or_p;
      p.not_p;

      p.bitwise_and_p;
      p.bitwise_or_p;
      p.bitwise_complement_p;
      p.bitwise_xor_p;
      p.left_shift_p;
      p.right_shift_p;

      p.x_p;
      p.y_p;
      p.int_lit_p
    ]

and random_ast (seed: int) (depth: int) (p: expr_p) =
  let state = Random.State.make [|seed|] in
  if depth >= max_depth then 
    Lazy.force (random_terminal state [p.x_p; p.y_p; p.int_lit_p])
  else     
    Lazy.force (random_expr seed state depth p)
