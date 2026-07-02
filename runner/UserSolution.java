package runner;

public class UserSolution implements Sorter {

    @Override
    public void sort(int[] arr) {

        int left = 0;
        int n = arr.length;
        int right = n - 1;
        int index = n / 3 + Math.min(5, n / 10);
        int target = arr[index];

        int result = -1;

        while (left <= right) {

            int mid = left + (right - left) / 2;

            if (arr[mid] == target) {
                result = mid;
                break;
            }

            if (arr[mid] < target)
                left = mid + 1;
            else
                right = mid - 1;
        }

        arr[0] = result;   // -1 if not found
    }
}