open Ast

let max_depth = Sys.argv.(3) |> int_of_string

(** Returns the last n elements of a list. *)
let last n l = 
  let rev = List.rev l in
  let rec last' n l =
    match n, l with
    | 0, _ -> []
    | _, [] -> []
    | _, x :: xs -> x :: last' (n - 1) xs in
  List.rev (last' n rev) 

(** Takes a Random state, a list of values, and a list of probabilities
    and returns a value from the list of values with the corresponding
    probability. *)
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

(** Generates a random integer literal. *)
let random_int_lit state =
  let n = Random.State.full_int state 100 in
  IntLit n

(** Generates a random leaf (terminal) of the AST. *)
let random_terminal state p = 
  let normalized_p = List.map (fun x -> x /. (List.fold_left (+.) 0.0 p)) p in
  choose state [lazy X; lazy Y; lazy (random_int_lit state); lazy True; lazy False] normalized_p

(** Generates a random node (non-terminal) of the AST. *)
let rec random_expr seed state depth p =
  choose state [
      lazy (Neg (random_ast (seed + 1) (depth + 1) p));
      lazy (Plus (random_ast (seed + 2) (depth + 1) p, random_ast (seed + 3) (depth + 1) p));
      lazy (Minus (random_ast (seed + 4) (depth + 1) p, random_ast (seed + 5) (depth + 1) p));
      lazy (Times (random_ast (seed + 6) (depth + 1) p, random_ast (seed + 7) (depth + 1) p));
      lazy (LessThan (random_ast (seed + 12) (depth + 1) p, random_ast (seed + 13) (depth + 1) p));
      lazy (LessEqual (random_ast (seed + 14) (depth + 1) p, random_ast (seed + 15) (depth + 1) p));
      lazy (GreaterThan (random_ast (seed + 16) (depth + 1) p, random_ast (seed + 17) (depth + 1) p));
      lazy (GreaterEqual (random_ast (seed + 18) (depth + 1) p, random_ast (seed + 19) (depth + 1) p));
      lazy (Equal (random_ast (seed + 20) (depth + 1) p, random_ast (seed + 21) (depth + 1) p));
      lazy (NotEqual (random_ast (seed + 22) (depth + 1) p, random_ast (seed + 23) (depth + 1) p));

      lazy (Not (random_ast (seed + 28) (depth + 1) p));

      lazy (BitwiseAnd (random_ast (seed + 29) (depth + 1) p, random_ast (seed + 30) (depth + 1) p));
      lazy (BitwiseOr (random_ast (seed + 31) (depth + 1) p, random_ast (seed + 32) (depth + 1) p));
      lazy (BitwiseComplement (random_ast (seed + 33) (depth + 1) p));
      lazy (BitwiseXor (random_ast (seed + 34) (depth + 1) p, random_ast (seed + 35) (depth + 1) p));
      lazy (LeftShift (random_ast (seed + 36) (depth + 1) p, random_ast (seed + 37) (depth + 1) p));
      lazy (RightShift (random_ast (seed + 38) (depth + 1) p, random_ast (seed + 39) (depth + 1) p));

      lazy X;
      lazy Y;
      lazy (random_int_lit state);
      lazy True;
      lazy False
    ] p

(** Generates a random AST. *)
and random_ast seed depth p =
  let state = Random.State.make [|seed|] in
  if depth >= max_depth then 
    let terminals_p = last 5 p in
    Lazy.force (random_terminal state terminals_p)
  else
    Lazy.force (random_expr seed state depth p)

(** Generates a random distribution of nodes in the AST. *)
let random_distribution seed =
  let state = Random.State.make [|seed|] in
  let random_list = List.init 22 (fun _ -> Random.State.float state 1.0) in
  let normalized_list = List.map (fun x -> x /. (List.fold_left (+.) 0.0 random_list)) random_list in
  normalized_list
  