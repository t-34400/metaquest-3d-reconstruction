import os
import multiprocessing


class ParallelWorker:
    def __init__(self, func, default=None):
        self.func = func
        self.default = default

    def __call__(self, args):
        try:
            if isinstance(args, tuple):
                return self.func(*args)
            else:
                return self.func(args)
        except Exception as e:
            print(f"[Error] {self.func.__name__} failed: {e}")
            return self.default


def parallel_map(
    func,
    args_list,
    max_workers=None,
    use_multiprocessing=True,
    context="spawn",
    default_on_error=None,
    show_progress=False,
    desc=None,
):
    worker = ParallelWorker(func, default_on_error)

    if not use_multiprocessing:
        results = []

        args_iter = args_list
        if show_progress:
            from tqdm import tqdm
            args_iter = tqdm(args_list, total=len(args_list), desc=desc)

        for args in args_iter:
            try:
                results.append(worker(args))
            except Exception as e:
                print(f"[Error] {func.__name__} failed: {e}")
                results.append(default_on_error)

        return results

    os.environ["OMP_NUM_THREADS"] = "1"

    if max_workers is None:
        max_workers = max(1, min(multiprocessing.cpu_count() - 1, len(args_list)))

    ctx = multiprocessing.get_context(context)

    with ctx.Pool(processes=max_workers) as pool:
        if show_progress:
            from tqdm import tqdm
            results = list(tqdm(pool.imap_unordered(worker, args_list), total=len(args_list), desc=desc))
        else:
            results = pool.map(worker, args_list)

    return results
