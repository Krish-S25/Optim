package runner;

import java.io.FileWriter;
import java.io.IOException;
import java.util.Random;
import java.util.Arrays;

public class BenchmarkDriver {
    public static void main(String[] args) {
        Sorter sorter = new UserSolution();
        Sorter emptySorter = new Sorter() {
            @Override
            public void sort(int[] arr) {}
        };
        Random rand = new Random(42);
        
        // Parse CLI arguments (defaults fall back to standard int ranges)
        String dataType = args.length > 0 ? args[0] : "integer";
        String arrayState = args.length > 1 ? args[1] : "random";
        int rangeStart = args.length > 2 ? Integer.parseInt(args[2]) : 0;
        int rangeEnd = args.length > 3 ? Integer.parseInt(args[3]) : 100;

        System.out.println("Configuring Array Generator: [" + arrayState + "] from " + rangeStart + " to " + rangeEnd);

        /* 0. Correctness Check Disabled
        System.out.println("Running Correctness Check on small array...");
        int[] testArr = generateArray(15, "random", rangeStart, rangeEnd, rand);
        int[] testArrCopy = Arrays.copyOf(testArr, testArr.length);
        sorter.sort(testArr);
        Arrays.sort(testArrCopy);
        if (!Arrays.equals(testArr, testArrCopy)) {
            System.err.println("Correctness Error: Your algorithm did not sort the array correctly!");
            System.exit(1);
        }
        System.out.println("Correctness Check Passed.");
        */

        // 1. JVM Warmup Phase
        System.out.println("Executing native JIT optimizer passes...");
        int warmupSize = 25; // Drastically reduced to prevent O(N^3) from freezing during the 5000 warmup passes!
        for (int i = 0; i < 5000; i++) {
            int[] warmupArr = generateArray(warmupSize, arrayState, rangeStart, rangeEnd, rand);
            sorter.sort(warmupArr);
        }
        
        System.gc(); // Purge warmup garbage
        try { Thread.sleep(50); } catch (Exception e) {} // Let JVM breathe

        // 2. STAGE ONE: Progressive Heuristic Probe
        System.out.println("Running Stage 1: Progressive Heuristic Probe...");
        
        // Phase 1: Small scale probe to catch O(N^2) and O(N^3) safely
        int[] clusterSmall = {100, 120, 140};
        int[] clusterMedium = {400, 480, 560};
        
        long timeSmall = measureClusterMedian(sorter, clusterSmall, arrayState, rangeStart, rangeEnd, rand);
        long timeMedium = measureClusterMedian(sorter, clusterMedium, arrayState, rangeStart, rangeEnd, rand);
        
        double growthRatio = (double) timeMedium / Math.max(1, timeSmall);
        
        System.out.printf("Initial Probe Ratio: %.2f for a 4.0x scale jump\n", growthRatio);
        
        int[] targetSizes;
        int sampleRuns;
        
        if (growthRatio >= 55.0) {
            System.out.println("Classification: Superlinear (O(N^3) detected). Capping max array size.");
            targetSizes = new int[]{ 100, 250, 400, 600, 800, 1000, 1200 };
            sampleRuns = 10; 
        } 
        else if (growthRatio >= 12.0) {
            System.out.println("Classification: Quadratic (O(N^2) detected). Scaling to medium arrays.");
            targetSizes = new int[]{ 100, 300, 600, 1000, 1800, 2500, 3500 };
            sampleRuns = 20; 
        } 
        else {
            // Phase 2: Massive scale probe for fast algorithms to bypass O(K) allocation noise
            System.out.println("Fast algorithm detected. Running High-Fidelity Massive Probe...");
            int[] clusterLarge = {10000, 12000, 14000};
            int[] clusterMassive = {40000, 48000, 56000};
            
            long timeLarge = measureClusterMedian(sorter, clusterLarge, arrayState, rangeStart, rangeEnd, rand);
            long timeMassive = measureClusterMedian(sorter, clusterMassive, arrayState, rangeStart, rangeEnd, rand);
            
            growthRatio = (double) timeMassive / Math.max(1, timeLarge);
            System.out.printf("High-Fidelity Probe Ratio: %.2f for a 4.0x scale jump\n", growthRatio);
            
            if (growthRatio >= 3.0) {
                System.out.println("Classification: Linear (O(N) / O(N log N) detected). Scaling to large arrays.");
                targetSizes = new int[]{ 1000, 5000, 10000, 20000, 40000, 70000, 100000 };
                sampleRuns = 50;
            } 
            else {
                System.out.println("Classification: Sublinear (O(1) / O(log N) detected). Scaling to massive arrays.");
                targetSizes = new int[]{ 1000, 5000, 10000, 50000, 100000, 250000, 500000, 1000000, 2500000, 5000000 };
                sampleRuns = 500;
            }
        }

        // 3.5 JIT Dry Run for final sizes
        System.out.println("Stabilizing JIT for target scales...");
        for (int size : targetSizes) {
            for (int k = 0; k < 5; k++) {
                int[] arr = generateArray(size, arrayState, rangeStart, rangeEnd, rand);
                sorter.sort(arr);
            }
        }
        System.gc();
        try { Thread.sleep(50); } catch (Exception e) {}

        // 4. Final Empirical Tracking Loop
        try (FileWriter writer = new FileWriter("metrics.csv")) {
            writer.write("size,runtime_ms\n");
            System.out.println("Running Stage 2: High-Precision Final Tracking...");

            for (int size : targetSizes) {
                // 1. Generate single Master Array for this size
                int[] masterArray = generateArray(size, arrayState, rangeStart, rangeEnd, rand);
                
                // 2. Measure overhead baseline (clone + method dispatch + timer)
                double baselineMs = measureAndEnforceSafety(emptySorter, size, sampleRuns, masterArray);
                
                // 3. Measure raw runtime
                double rawMs = measureAndEnforceSafety(sorter, size, sampleRuns, masterArray);
                
                if (rawMs < 0) {
                    System.out.println("Safety Valve triggered. Auto-terminating scale climb.");
                    break; 
                }

                // 4. Subtract baseline to isolate pure algorithmic complexity
                double trueMs = Math.max(0.000001, rawMs - baselineMs);

                writer.write(size + "," + String.format("%.6f", trueMs) + "\n");
            }
            System.out.println("Dynamic coordinate matrix saved cleanly.");

        } catch (IOException e) {
            System.err.println("Critical write fault: " + e.getMessage());
        }
    }

    private static int[] generateArray(int size, String state, int start, int end, Random rand) {
        int[] arr = new int[size];
        int bound = end - start;
        if (bound <= 0) bound = 1;
        
        for (int i = 0; i < size; i++) {
            arr[i] = rand.nextInt(bound) + start;
        }
        
        if (state.equals("sorted") || state.equals("nearly_sorted")) {
            Arrays.sort(arr);
        }
        
        if (state.equals("nearly_sorted")) {
            int swaps = Math.min(size / 2, 5); // Max 5 adjacent swaps to remain truly O(N)
            for (int i = 0; i < swaps; i++) {
                int idx = rand.nextInt(size - 1);
                int temp = arr[idx];
                arr[idx] = arr[idx+1];
                arr[idx+1] = temp;
            }
        }
        
        return arr;
    }

    private static long measureMedianProbe(Sorter sorter, int size, String state, int start, int end, Random rand) {
        long[] results = new long[5];
        for (int r = 0; r < 5; r++) {
            long passTotal = 0;
            for (int k = 0; k < 20; k++) {
                int[] arr = generateArray(size, state, start, end, rand);
                long startTime = System.nanoTime();
                sorter.sort(arr);
                long endTime = System.nanoTime();
                
                long duration = (endTime - startTime);
                passTotal += duration;
                if (duration > 200_000_000L) return duration * (20 - k); // Fast early abort for O(N^3) at 200ms
            }
            results[r] = passTotal;
        }
        Arrays.sort(results);
        return results[2]; 
    }

    private static long measureClusterMedian(Sorter sorter, int[] sizes, String state, int start, int end, Random rand) {
        long[] results = new long[sizes.length];
        for (int i = 0; i < sizes.length; i++) {
            results[i] = measureMedianProbe(sorter, sizes[i], state, start, end, rand);
        }
        Arrays.sort(results);
        return results[sizes.length / 2];
    }

    private static double measureAndEnforceSafety(Sorter sorter, int size, int targetRuns, int[] masterArray) {
        long accumulatedNano = 0;
        int actualRuns = 0;

        for (int r = 0; r < targetRuns; r++) {
            // Instantaneous memory pool copy
            int[] arr = Arrays.copyOf(masterArray, size);
            
            long startTime = System.nanoTime();
            sorter.sort(arr);
            long endTime = System.nanoTime();

            long duration = (endTime - startTime);
            accumulatedNano += duration;
            actualRuns++;

            if (duration > 1_000_000_000L) return -1.0; 
        }
        
        return (accumulatedNano / (double) actualRuns) / 1_000_000.0;
    }
}
