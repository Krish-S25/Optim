package runner;
import java.util.Random;
import java.util.Arrays;

public class DryRunDriver {
    public static void main(String[] args) {
        Sorter sorter = new UserSolution();
        Random rand = new Random(42);
        
        // 1. Functional output check on N=15
        int[] arr15 = new int[15];
        for(int i=0; i<15; i++) arr15[i] = rand.nextInt(Math.max(1, 60 - -20)) + -20;
        System.out.println("INPUT : " + Arrays.toString(arr15));
        
        // Warmup JIT slightly to stabilize initial timer
        for(int i=0; i<100; i++) {
            int[] warmup = new int[10];
            for(int j=0; j<10; j++) warmup[j] = rand.nextInt(Math.max(1, 60 - -20)) + -20;
            sorter.sort(warmup);
        }
        
        sorter.sort(arr15);
        System.out.println("OUTPUT: " + Arrays.toString(arr15));
        
        // 2. Exponential Growth Check (15 vs 25)
        long[] times = new long[3];
        int[] sizes = {15, 20, 25};
        for (int i = 0; i < 3; i++) {
            int[] testArr = new int[sizes[i]];
            for(int j=0; j<sizes[i]; j++) testArr[j] = rand.nextInt(Math.max(1, 60 - -20)) + -20;
            
            long start = System.nanoTime();
            sorter.sort(testArr);
            times[i] = System.nanoTime() - start;
        }
        
        long t15 = Math.max(1, times[0]);
        long t25 = Math.max(1, times[2]);
        double growth = (double) t25 / t15;
        
        // Cubic O(N^3) growth from 15 to 25 is (25/15)^3 = 4.6x
        // If growth > 10.0x, it is definitively super-polynomial (exponential)
        if (growth > 10.0) {
            System.err.println("\n[!] Exponential Complexity Detected! Growth ratio " + String.format("%.1fx", growth) + " vastly exceeds polynomial limits.");
            System.exit(1);
        }
    }
}